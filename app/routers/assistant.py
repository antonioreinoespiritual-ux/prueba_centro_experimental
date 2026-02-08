from __future__ import annotations

import json
import re
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, or_, select, func
from sqlalchemy.orm import Session

from .. import ai, schemas, crud
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
    AssistantDraft,
)

router = APIRouter()

_RATE_LIMIT_BUCKET: dict[str, list[float]] = {}
_RATE_LIMIT_WINDOW_S = 60
_RATE_LIMIT_MAX = 12
_COOLDOWN_UNTIL: float | None = None

_CONFIRM_PHRASES = (
    "confirmar creación",
    "confirmar creacion",
    "confirmar record",
    "confirmar hipótesis",
    "confirmar hipotesis",
    "listo, crea",
    "listo crea",
    "crea la hipótesis",
    "crea la hipotesis",
    "crea el record",
    "confirmar creación de record",
)

_DRAFT_CANCEL_PHRASES = (
    "cancelar borrador",
    "cancelar",
    "borrar borrador",
    "borrar",
    "eliminar",
    "descartar borrador",
    "reiniciar borrador",
    "eliminar borrador",
    "eliminar borrador de hipotesis",
    "eliminar borrador de hipótesis",
    "reiniciar hipotesis",
    "reiniciar hipótesis",
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _check_rate_limit(client_key: str) -> None:
    now = time.time()
    if _COOLDOWN_UNTIL and now < _COOLDOWN_UNTIL:
        remaining = int(_COOLDOWN_UNTIL - now)
        raise HTTPException(
            status_code=429,
            detail=f"Cooldown activo. Intenta nuevamente en {remaining}s.",
        )
    bucket = _RATE_LIMIT_BUCKET.setdefault(client_key, [])
    bucket[:] = [ts for ts in bucket if now - ts < _RATE_LIMIT_WINDOW_S]
    if len(bucket) >= _RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    bucket.append(now)


def _set_cooldown_from_error(error_message: str) -> None:
    global _COOLDOWN_UNTIL
    match = re.search(r"in (?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", error_message)
    if not match:
        return
    hours = float(match.group(1) or 0)
    minutes = float(match.group(2) or 0)
    seconds = float(match.group(3) or 0)
    total_seconds = hours * 3600 + minutes * 60 + seconds
    if total_seconds <= 0:
        return
    _COOLDOWN_UNTIL = time.time() + total_seconds


def _compact_text(value: str, limit: int = 400) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit]}…"


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _is_confirm_message(message: str) -> bool:
    lowered = _normalize_text(message)
    return any(phrase in lowered for phrase in _CONFIRM_PHRASES)


def _is_cancel_message(message: str) -> bool:
    lowered = _normalize_text(message)
    return any(phrase in lowered for phrase in _DRAFT_CANCEL_PHRASES)


def _is_draft_intent(message: str) -> str | None:
    lowered = _normalize_text(message)
    if "hipotesis" in lowered or "hipótesis" in lowered:
        return "experiment"
    if "record" in lowered or "récord" in lowered or "prueba" in lowered:
        return "record"
    if "borrador" in lowered:
        return "record"
    return None


def _get_draft(db: Session, conversation_id: str) -> AssistantDraft | None:
    return db.execute(
        select(AssistantDraft)
        .where(AssistantDraft.conversation_id == conversation_id)
        .order_by(desc(AssistantDraft.updated_at), desc(AssistantDraft.created_at))
    ).scalar_one_or_none()


def _save_draft(db: Session, conversation_id: str, draft_type: str, payload: dict) -> AssistantDraft:
    existing = _get_draft(db, conversation_id)
    payload_json = json.dumps(payload, ensure_ascii=False)
    if existing:
        existing.draft_type = draft_type
        existing.payload_json = payload_json
        existing.updated_at = datetime.utcnow()
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    draft = AssistantDraft(
        conversation_id=conversation_id,
        draft_type=draft_type,
        payload_json=payload_json,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def _clear_draft(db: Session, conversation_id: str) -> None:
    draft = _get_draft(db, conversation_id)
    if draft:
        db.delete(draft)
        db.commit()


def _pretty_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _draft_missing_fields(draft_type: str, draft: dict) -> list[str]:
    missing: list[str] = []
    if draft_type == "experiment":
        if not draft.get("project_name"):
            missing.append("project_name")
        if not draft.get("hypothesis"):
            missing.append("hypothesis")
        if not draft.get("traffic_type"):
            missing.append("traffic_type")
        if not draft.get("metric_x"):
            missing.append("metric_x")
        if not draft.get("primary_metric"):
            missing.append("primary_metric")
        if not draft.get("threshold_operator"):
            missing.append("threshold_operator")
        if draft.get("threshold_value") is None:
            missing.append("threshold_value")
        if not draft.get("threshold_type"):
            missing.append("threshold_type")
        if draft.get("volume_min_value") is None:
            missing.append("volume_min_value")
        if not draft.get("volume_unit"):
            missing.append("volume_unit")
    if draft_type == "record":
        if not draft.get("experiment_id"):
            missing.append("experiment_id")
        if not (draft.get("public_id") or draft.get("publico")):
            missing.append("public_id/publico")
        if not draft.get("execution_type"):
            missing.append("execution_type")
        if not draft.get("session_id"):
            missing.append("session_id")
    return missing


def _render_draft_response(draft_type: str, draft: dict, missing: list[str]) -> str:
    title = "Borrador de hipótesis" if draft_type == "experiment" else "Borrador de record"
    status_line = f"Estado actual: {draft.get('experiment_status') or draft.get('record_status') or 'draft'}"
    missing_line = "Faltan datos: " + ", ".join(missing) if missing else "Listo para confirmar creación."
    instructions = (
        "Puedes pedir cambios (ej: \"cambia el umbral a 20%\"), o confirmar con "
        "\"Listo, crea la hipótesis\" / \"Listo, crea el record\"."
    )
    return "\n".join(
        [
            title,
            status_line,
            missing_line,
            "",
            "Borrador actual:",
            _pretty_json(draft),
            "",
            instructions,
        ]
    )


def _merge_draft(existing: dict, incoming: dict) -> dict:
    merged = dict(existing)
    for key, value in incoming.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        merged[key] = value
    return merged


def _sanitize_experiment_draft(draft: dict) -> dict:
    cleaned = dict(draft)
    disallowed = {
        "hook_type",
        "hook_text",
        "cta_type",
        "cta_text",
        "execution_type",
        "record_name",
        "public_id",
        "publico",
        "record_status",
        "creative_id",
        "session_id",
        "iteration_number",
    }
    for key in disallowed:
        cleaned.pop(key, None)
    return cleaned


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


def _build_openclaw_context(db: Session) -> dict:
    experiments = list(
        db.execute(
            select(Experiment).order_by(desc(Experiment.updated_at), desc(Experiment.created_at)).limit(100)
        ).scalars()
    )
    publics = list(
        db.execute(
            select(Public).order_by(desc(Public.updated_at), desc(Public.created_at)).limit(100)
        ).scalars()
    )
    records = list(
        db.execute(
            select(ExperimentRecord)
            .order_by(desc(ExperimentRecord.updated_at), desc(ExperimentRecord.created_at))
            .limit(120)
        ).scalars()
    )
    return {
        "experiments": [
            {
                "id": exp.id,
                "project_name": exp.project_name,
                "hypothesis": exp.hypothesis,
                "metric_x": exp.metric_x,
                "primary_metric": exp.primary_metric,
                "traffic_type": exp.traffic_type,
                "status": exp.experiment_status,
            }
            for exp in experiments
        ],
        "projects": sorted({exp.project_name for exp in experiments if exp.project_name}),
        "publics": [
            {"id": public.id, "name": public.name, "description": public.description}
            for public in publics
        ],
        "records_recent": [
            {
                "id": record.id,
                "experiment_id": record.experiment_id,
                "record_name": record.record_name,
                "execution_type": record.execution_type,
                "publico": record.publico,
                "hook_text": record.hook_text,
                "hook_type": record.hook_type,
                "cta_text": record.cta_text,
                "cta_type": record.cta_type,
                "record_status": record.record_status,
                "created_at": record.created_at.isoformat(),
            }
            for record in records
        ],
        "allowed_enums": {
            "traffic_type": list(schemas.TrafficType.__args__),
            "hypothesis_type": list(schemas.HypothesisType.__args__),
            "primary_metric": list(schemas.PrimaryMetric.__args__),
            "threshold_type": list(schemas.ThresholdType.__args__),
            "threshold_operator": list(schemas.ThresholdOperator.__args__),
            "execution_type": list(schemas.ExecutionType.__args__),
            "hook_type": list(schemas.HookType.__args__),
            "cta_type": list(schemas.CtaType.__args__),
        },
    }


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

    draft = _get_draft(db, conversation_id)
    draft_type = draft.draft_type if draft else _is_draft_intent(message)
    if _is_cancel_message(message):
        _clear_draft(db, conversation_id)
        return schemas.ChatResponse(
            answer="Borrador descartado. Puedes iniciar uno nuevo cuando quieras.",
            citations=citations,
        )

    if draft_type:
        openclaw_context = _build_openclaw_context(db)
        existing_payload = json.loads(draft.payload_json) if draft else {}
        try:
            draft_response = ai.generate_openclaw_draft(
                message=message,
                draft_type=draft_type,
                context=openclaw_context,
                existing_draft=existing_payload.get("draft"),
                model_override=payload.model,
            )
        except ai.GroqError as exc:
            _set_cooldown_from_error(str(exc))
            answer = _fallback_answer(context_json, str(exc))
            return schemas.ChatResponse(answer=answer, citations=citations)

        incoming_draft = draft_response.get("draft", {})
        merged_draft = _merge_draft(existing_payload.get("draft", {}), incoming_draft)

        if draft_type == "experiment":
            merged_draft = _sanitize_experiment_draft(merged_draft)
            merged_draft.setdefault("experiment_status", "draft")
        if draft_type == "record":
            merged_draft.setdefault("record_status", "draft")
            merged_draft.setdefault(
                "session_id",
                existing_payload.get("draft", {}).get("session_id")
                or f"openclaw-{int(time.time())}",
            )

        missing = _draft_missing_fields(draft_type, merged_draft)
        _save_draft(
            db,
            conversation_id,
            draft_type,
            {
                "draft": merged_draft,
                "missing_fields": missing,
                "notes": draft_response.get("notes"),
            },
        )

        if _is_confirm_message(message):
            if missing:
                return schemas.ChatResponse(
                    answer=_render_draft_response(draft_type, merged_draft, missing),
                    citations=citations,
                )
            if draft_type == "experiment":
                exp_payload = schemas.ExperimentCreate(
                    project_name=merged_draft["project_name"],
                    hypothesis=merged_draft["hypothesis"],
                    traffic_type=merged_draft["traffic_type"],
                    contexto=merged_draft.get("contexto"),
                    hypothesis_type=merged_draft.get("hypothesis_type"),
                    independent_variable=merged_draft.get("independent_variable"),
                    metric_x=merged_draft.get("metric_x"),
                    primary_metric=merged_draft.get("primary_metric"),
                    validation_threshold=merged_draft.get("validation_threshold"),
                    threshold_value=merged_draft.get("threshold_value"),
                    threshold_type=merged_draft.get("threshold_type"),
                    threshold_operator=merged_draft.get("threshold_operator"),
                    experiment_status="running",
                    min_volume=merged_draft.get("min_volume"),
                    volume_min_value=merged_draft.get("volume_min_value"),
                    volume_unit=merged_draft.get("volume_unit"),
                )
                exp = crud.create_experiment(db, exp_payload)
                crud.create_documentation_note(
                    db,
                    "experiment",
                    exp.id,
                    f"Hipótesis creada vía asistente. Timestamp: {datetime.utcnow().isoformat()}",
                )
                _clear_draft(db, conversation_id)
                answer = (
                    f"Hipótesis creada con ID {exp.id}. Estado inicial: {exp.experiment_status}.\n"
                    "Si quieres, ahora podemos crear records para esta hipótesis."
                )
                return schemas.ChatResponse(answer=answer, citations=citations)
            if draft_type == "record":
                record_payload = schemas.RecordCreate(
                    experiment_id=merged_draft["experiment_id"],
                    session_id=merged_draft["session_id"],
                    iteration_number=merged_draft.get("iteration_number"),
                    contexto_record=merged_draft.get("contexto_record"),
                    execution_type=merged_draft.get("execution_type"),
                    record_name=merged_draft.get("record_name"),
                    public_id=merged_draft.get("public_id"),
                    publico=merged_draft.get("publico"),
                    hook_text=merged_draft.get("hook_text"),
                    hook_type=merged_draft.get("hook_type"),
                    cta_text=merged_draft.get("cta_text"),
                    cta_type=merged_draft.get("cta_type"),
                    creative_id=merged_draft.get("creative_id"),
                    record_status="collecting",
                )
                record = crud.create_record(db, record_payload)
                crud.create_documentation_note(
                    db,
                    "record",
                    record.id,
                    f"Record creado vía asistente. Timestamp: {datetime.utcnow().isoformat()}",
                )
                _clear_draft(db, conversation_id)
                answer = (
                    f"Record creado con ID {record.id}. Estado inicial: {record.record_status}.\n"
                    "Ya está listo para recibir métricas."
                )
                return schemas.ChatResponse(answer=answer, citations=citations)

        return schemas.ChatResponse(
            answer=_render_draft_response(draft_type, merged_draft, missing),
            citations=citations,
        )

    memory_trigger = None
    lowered = message.lower().strip()
    if lowered.startswith("memoriza:") or lowered.startswith("guardar:"):
        memory_trigger = message.split(":", 1)[-1].strip()

    model_override = payload.model.strip() if payload.model else None
    try:
        answer = ai.generate_assistant_reply(context_json, message, model_override=model_override)
    except ai.GroqError as exc:
        _set_cooldown_from_error(str(exc))
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
