from __future__ import annotations

import json
import re
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, or_, select, func
from sqlalchemy.orm import Session

from .. import ai, schemas
from ..database import SessionLocal
from ..models import (
    Experiment,
    ExperimentRecord,
    Public,
    DocumentationNote,
    Documentation,
    AIAnalysis,
    ChatMemory,
    ChatMessage,
)

router = APIRouter()

_RATE_LIMIT_BUCKET: dict[str, list[float]] = {}
_RATE_LIMIT_WINDOW_S = 60
_RATE_LIMIT_MAX = 12


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _check_rate_limit(client_key: str) -> None:
    now = time.time()
    bucket = _RATE_LIMIT_BUCKET.setdefault(client_key, [])
    bucket[:] = [ts for ts in bucket if now - ts < _RATE_LIMIT_WINDOW_S]
    if len(bucket) >= _RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    bucket.append(now)


def _compact_text(value: str, limit: int = 400) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit]}…"


def _extract_ids(message: str) -> dict[str, list[int]]:
    patterns = {
        "record": r"(?:record|récord)\s*#?\s*(\d+)",
        "experiment": r"(?:experimento|exp)\s*#?\s*(\d+)",
        "hypothesis": r"(?:hip[oó]tesis|hyp)\s*#?\s*(\d+)",
        "public": r"(?:p[úu]blico|publico)\s*#?\s*(\d+)",
    }
    results: dict[str, list[int]] = {key: [] for key in patterns}
    for key, pattern in patterns.items():
        for match in re.findall(pattern, message, flags=re.IGNORECASE):
            try:
                results[key].append(int(match))
            except ValueError:
                continue
    return results


def _keyword_terms(message: str) -> list[str]:
    tokens = re.findall(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9]+", message.lower())
    stopwords = {"que", "para", "los", "las", "una", "unos", "unas", "con", "sin", "del", "por", "pero", "sobre"}
    terms = [token for token in tokens if len(token) > 3 and token not in stopwords]
    return terms[:5]


def _serialize_record(record: ExperimentRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "session_id": record.session_id,
        "record_name": record.record_name,
        "status": record.record_status,
        "execution_type": record.execution_type,
        "public_id": record.public_id,
        "publico": record.publico,
        "clicks": record.clicks,
        "views": record.views,
        "ctr": record.ctr,
        "purchase": record.purchase,
        "retention_pct": record.retention_pct,
        "avg_watch_time": record.avg_watch_time,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def _build_context(
    db: Session,
    message: str,
    conversation_id: str | None,
) -> tuple[str, list[str]]:
    citations: list[str] = []

    experiments = list(
        db.execute(
            select(Experiment).order_by(desc(Experiment.updated_at), desc(Experiment.created_at)).limit(50)
        ).scalars()
    )
    records = list(
        db.execute(
            select(ExperimentRecord).order_by(desc(ExperimentRecord.updated_at), desc(ExperimentRecord.created_at)).limit(50)
        ).scalars()
    )
    publics = list(
        db.execute(select(Public).order_by(Public.name).limit(50)).scalars()
    )
    notes = list(
        db.execute(
            select(DocumentationNote)
            .order_by(desc(DocumentationNote.updated_at), desc(DocumentationNote.created_at))
            .limit(20)
        ).scalars()
    )
    analyses = list(
        db.execute(select(AIAnalysis).order_by(desc(AIAnalysis.created_at)).limit(15)).scalars()
    )
    memories = list(
        db.execute(select(ChatMemory).order_by(desc(ChatMemory.updated_at), desc(ChatMemory.created_at)).limit(15)).scalars()
    )
    conversation_messages: list[ChatMessage] = []
    if conversation_id:
        conversation_messages = list(
            db.execute(
                select(ChatMessage)
                .where(ChatMessage.conversation_id == conversation_id)
                .order_by(desc(ChatMessage.created_at))
                .limit(8)
            ).scalars()
        )

    ids = _extract_ids(message)
    matched_records: list[ExperimentRecord] = []
    matched_experiments: list[Experiment] = []
    matched_publics: list[Public] = []

    if ids["record"]:
        matched_records.extend(
            list(db.execute(select(ExperimentRecord).where(ExperimentRecord.id.in_(ids["record"]))).scalars())
        )
    if ids["experiment"] or ids["hypothesis"]:
        exp_ids = ids["experiment"] + ids["hypothesis"]
        matched_experiments.extend(
            list(db.execute(select(Experiment).where(Experiment.id.in_(exp_ids))).scalars())
        )
    if ids["public"]:
        matched_publics.extend(
            list(db.execute(select(Public).where(Public.id.in_(ids["public"]))).scalars())
        )

    terms = _keyword_terms(message)
    if terms:
        or_clauses_records = []
        or_clauses_experiments = []
        or_clauses_publics = []
        for term in terms:
            like = f"%{term}%"
            or_clauses_records.extend(
                [
                    ExperimentRecord.record_name.ilike(like),
                    ExperimentRecord.hook_text.ilike(like),
                    ExperimentRecord.cta_text.ilike(like),
                    ExperimentRecord.publico.ilike(like),
                    ExperimentRecord.session_id.ilike(like),
                ]
            )
            or_clauses_experiments.extend(
                [Experiment.project_name.ilike(like), Experiment.hypothesis.ilike(like)]
            )
            or_clauses_publics.append(Public.name.ilike(like))

        if or_clauses_records:
            matched_records.extend(
                list(
                    db.execute(
                        select(ExperimentRecord)
                        .where(or_(*or_clauses_records))
                        .order_by(desc(ExperimentRecord.updated_at), desc(ExperimentRecord.created_at))
                        .limit(10)
                    ).scalars()
                )
            )
        if or_clauses_experiments:
            matched_experiments.extend(
                list(
                    db.execute(
                        select(Experiment)
                        .where(or_(*or_clauses_experiments))
                        .order_by(desc(Experiment.updated_at), desc(Experiment.created_at))
                        .limit(10)
                    ).scalars()
                )
            )
        if or_clauses_publics:
            matched_publics.extend(
                list(
                    db.execute(
                        select(Public)
                        .where(or_(*or_clauses_publics))
                        .order_by(Public.name)
                        .limit(10)
                    ).scalars()
                )
            )

    records_summary = [_serialize_record(record) for record in records]
    matched_records_summary = [_serialize_record(record) for record in matched_records]

    context = {
        "summary": {
            "experiments_total": db.execute(select(func.count(Experiment.id))).scalar_one(),
            "records_total": db.execute(select(func.count(ExperimentRecord.id))).scalar_one(),
            "publics_total": db.execute(select(func.count(Public.id))).scalar_one(),
            "documentation_notes_total": db.execute(select(func.count(DocumentationNote.id))).scalar_one(),
            "ai_analyses_total": db.execute(select(func.count(AIAnalysis.id))).scalar_one(),
        },
        "experiments_recent": [
            {
                "id": exp.id,
                "project_name": exp.project_name,
                "hypothesis": _compact_text(exp.hypothesis, 320),
                "status": exp.experiment_status,
                "hypothesis_type": exp.hypothesis_type,
                "traffic_type": exp.traffic_type,
                "updated_at": exp.updated_at.isoformat() if exp.updated_at else None,
            }
            for exp in experiments
        ],
        "records_recent": records_summary,
        "publics_recent": [
            {"id": public.id, "name": public.name, "description": _compact_text(public.description or "", 240)}
            for public in publics
        ],
        "documentation_notes_recent": [
            {
                "id": note.id,
                "entity_type": doc.entity_type if (doc := db.get(Documentation, note.documentation_id)) else None,
                "entity_id": doc.entity_id if doc else None,
                "body": _compact_text(note.body, 240),
                "created_at": note.created_at.isoformat(),
            }
            for note in notes
        ],
        "ai_analysis_recent": [
            {
                "id": analysis.id,
                "entity_type": analysis.entity_type,
                "entity_id": analysis.entity_id,
                "analysis_type": analysis.analysis_type,
                "created_at": analysis.created_at.isoformat(),
                "output": _compact_text(analysis.output, 280),
            }
            for analysis in analyses
        ],
        "memories": [
            {
                "id": memory.id,
                "type": memory.memory_type,
                "content": _compact_text(memory.content, 300),
                "references": memory.references_json,
            }
            for memory in memories
        ],
        "conversation_recent": [
            {
                "role": msg.role,
                "content": _compact_text(msg.content, 240),
                "created_at": msg.created_at.isoformat(),
            }
            for msg in reversed(conversation_messages)
        ],
        "matches": {
            "records": matched_records_summary,
            "experiments": [
                {
                    "id": exp.id,
                    "project_name": exp.project_name,
                    "hypothesis": _compact_text(exp.hypothesis, 320),
                    "status": exp.experiment_status,
                }
                for exp in matched_experiments
            ],
            "publics": [
                {"id": public.id, "name": public.name, "description": _compact_text(public.description or "", 240)}
                for public in matched_publics
            ],
        },
    }

    for rec in matched_records:
        citations.append(f"record:{rec.id}")
    for exp in matched_experiments:
        citations.append(f"experiment:{exp.id}")
    for public in matched_publics:
        citations.append(f"public:{public.id}")

    return json.dumps(context, ensure_ascii=False, indent=2), citations


def _fallback_answer(context_json: str, error_message: str) -> str:
    try:
        payload = json.loads(context_json)
    except json.JSONDecodeError:
        return (
            "No pude contactar la IA en este momento. "
            f"Detalle: {error_message}"
        )
    summary = payload.get("summary", {})
    experiments = payload.get("experiments_recent", [])
    records = payload.get("records_recent", [])
    publics = payload.get("publics_recent", [])
    parts = [
        "No pude contactar la IA en este momento, pero te dejo un resumen rápido:",
        f"- Experimentos totales: {summary.get('experiments_total', '—')}",
        f"- Records totales: {summary.get('records_total', '—')}",
        f"- Públicos totales: {summary.get('publics_total', '—')}",
    ]
    if experiments:
        parts.append(f"- Último experimento: {experiments[0].get('project_name', '—')}")
    if records:
        parts.append(f"- Último record: {records[0].get('record_name', records[0].get('id', '—'))}")
    if publics:
        parts.append(f"- Último público: {publics[0].get('name', '—')}")
    parts.append(f"Detalle del error: {error_message}")
    return "\n".join(parts)


@router.post("/assistant/chat", response_model=schemas.ChatResponse)
def assistant_chat(
    payload: schemas.ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")

    client_key = request.client.host if request.client else "unknown"
    _check_rate_limit(client_key)

    conversation_id = payload.conversation_id
    context_json, citations = _build_context(db, message, conversation_id)

    memory_trigger = None
    lowered = message.lower().strip()
    if lowered.startswith("memoriza:") or lowered.startswith("guardar:"):
        memory_trigger = message.split(":", 1)[-1].strip()

    try:
        answer = ai.generate_assistant_reply(context_json, message)
    except ai.GroqError as exc:
        answer = _fallback_answer(context_json, str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.add(
        ChatMessage(
            conversation_id=conversation_id,
            role="user",
            content=message,
        )
    )
    db.add(
        ChatMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
            references_json=json.dumps(citations, ensure_ascii=False) if citations else None,
        )
    )
    if memory_trigger:
        db.add(
            ChatMemory(
                memory_type="insight",
                content=memory_trigger,
                references_json=json.dumps(citations, ensure_ascii=False) if citations else None,
            )
        )
    auto_memory = (
        f"Pregunta: {_compact_text(message, 180)} | "
        f"Respuesta: {_compact_text(answer, 220)}"
    )
    db.add(
        ChatMemory(
            memory_type="auto_summary",
            content=auto_memory,
            references_json=json.dumps(citations, ensure_ascii=False) if citations else None,
        )
    )
    db.commit()

    return schemas.ChatResponse(answer=answer, citations=citations)
