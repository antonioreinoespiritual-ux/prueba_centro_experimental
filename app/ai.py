from __future__ import annotations

import json

import requests

from .config import get_groq_api_key, get_groq_api_url, get_groq_model
from .models import Experiment, ExperimentRecord, Documentation, AIAnalysis
from .schemas import ExperimentEvaluation


class GroqError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def _extract_error_message(body: str) -> str | None:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None
    error = payload.get("error")
    if not isinstance(error, dict):
        return None
    message = error.get("message")
    if isinstance(message, str):
        return message
    return None


def _record_to_payload(record: ExperimentRecord) -> dict:
    base = {
        "id": record.id,
        "session_id": record.session_id,
        "status": record.record_status,
        "execution_type": record.execution_type,
        "record_name": record.record_name,
        "created_at": record.created_at.isoformat(),
    }
    metrics_fields = [
        "clicks",
        "views",
        "likes",
        "comments",
        "shares",
        "saves",
        "views_finish_pct",
        "retention_pct",
        "avg_watch_time",
        "video_duration",
        "ctr",
        "cpc",
        "initiate_checkouts",
        "view_content",
        "lead_form",
        "purchase",
        "paid_video_duration",
        "live_viewers_peak",
        "live_avg_viewers",
        "live_duration",
        "live_new_followers",
    ]
    metrics: dict[str, float | int] = {}
    for field in metrics_fields:
        value = getattr(record, field, None)
        if value is not None:
            metrics[field] = value
    if metrics:
        base["metrics"] = metrics

    meta_fields = [
        "organic_piece_type",
        "video_url",
        "campaign_id",
        "ad_set_id",
        "ad_id",
        "hook_type",
        "hook_text",
        "cta_type",
        "cta_text",
        "creative_id",
    ]
    meta: dict[str, str] = {}
    for field in meta_fields:
        value = getattr(record, field, None)
        if value:
            meta[field] = value
    if meta:
        base["metadata"] = meta

    return base


def _build_prompt(experiment: Experiment, evaluation: ExperimentEvaluation, records: list[ExperimentRecord]) -> str:
    exp_payload = {
        "id": experiment.id,
        "project_name": experiment.project_name,
        "hypothesis": experiment.hypothesis,
        "traffic_type": experiment.traffic_type,
        "status": experiment.experiment_status,
        "hypothesis_type": experiment.hypothesis_type,
        "independent_variable": experiment.independent_variable,
        "primary_metric": experiment.primary_metric,
        "threshold_operator": experiment.threshold_operator,
        "threshold_value": experiment.threshold_value,
        "threshold_type": experiment.threshold_type,
        "volume_min_value": experiment.volume_min_value,
        "volume_unit": experiment.volume_unit,
    }
    eval_payload = evaluation.model_dump()
    record_payload = [_record_to_payload(record) for record in records]
    context = {
        "experiment": exp_payload,
        "evaluation": eval_payload,
        "records_count": len(records),
        "records": record_payload,
    }
    return json.dumps(context, ensure_ascii=False, indent=2)


def generate_experiment_analysis(
    experiment: Experiment,
    evaluation: ExperimentEvaluation,
    records: list[ExperimentRecord],
) -> str:
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY. Define it in the .env file.")

    payload = {
        "model": get_groq_model(),
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un analista senior de experimentos. Entrega un analisis "
                    "completo en español usando los datos disponibles. Aprende y adapta tus "
                    "conclusiones únicamente con el historial de records entregado en el contexto. "
                    "Incluye resumen ejecutivo, hallazgos clave, riesgos, recomendaciones accionables "
                    "y siguientes pasos."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Analiza el resultado de la evaluacion del experimento junto a todos sus records. "
                    "Usa el siguiente contexto JSON:\n"
                    f"{_build_prompt(experiment, evaluation, records)}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 900,
    }

    try:
        resp = requests.post(
            get_groq_api_url(),
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            timeout=45,
        )
    except requests.ConnectionError as exc:
        raise GroqError(f"Groq connection error: {exc}") from exc
    except requests.Timeout as exc:
        raise GroqError("Groq request timed out.") from exc
    except Exception as exc:
        raise GroqError(f"Groq request failed: {exc}") from exc

    if resp.status_code != 200:
        error_body = resp.text
        error_message = _extract_error_message(error_body)
        if resp.status_code == 402:
            raise GroqError(
                "Groq sin saldo. Agrega creditos o actualiza la API key.",
                status_code=402,
            )
        if error_message:
            raise GroqError(f"Groq error: {error_message}")
        raise GroqError(f"Groq HTTP error {resp.status_code}: {error_body}")

    body = resp.text

    try:
        response_data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise GroqError("Groq returned invalid JSON.") from exc

    content = (
        response_data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        raise GroqError("Groq response missing content.")
    return str(content).strip()


def generate_assistant_reply(
    context: str,
    message: str,
    model_override: str | None = None,
) -> str:
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY. Define it in the .env file.")

    payload = {
        "model": model_override or get_groq_model(),
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres el asistente del Centro Experimental. Respondes preguntas, resumes, "
                    "analizas y referencias datos reales del sistema. No inventas. No creas ni "
                    "editas entidades automáticamente. Si falta información, indícalo y pide el "
                    "mínimo necesario. Responde en español y apóyate exclusivamente en el contexto."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Contexto actual del Centro Experimental (usa solo esta informacion):\n"
                    f"{context}\n\nPregunta del usuario:\n{message}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 900,
    }

    try:
        resp = requests.post(
            get_groq_api_url(),
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            timeout=45,
        )
    except requests.ConnectionError as exc:
        raise GroqError(f"Groq connection error: {exc}") from exc
    except requests.Timeout as exc:
        raise GroqError("Groq request timed out.") from exc
    except Exception as exc:
        raise GroqError(f"Groq request failed: {exc}") from exc

    if resp.status_code != 200:
        error_body = resp.text
        error_message = _extract_error_message(error_body)
        if resp.status_code == 402:
            raise GroqError(
                "Groq sin saldo. Agrega creditos o actualiza la API key.",
                status_code=402,
            )
        if error_message:
            raise GroqError(f"Groq error: {error_message}")
        raise GroqError(f"Groq HTTP error {resp.status_code}: {error_body}")

    body = resp.text

    try:
        response_data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise GroqError("Groq returned invalid JSON.") from exc

    content = (
        response_data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        raise GroqError("Groq response missing content.")
    return str(content).strip()


def generate_openclaw_draft(
    message: str,
    draft_type: str,
    context: dict,
    existing_draft: dict | None = None,
    model_override: str | None = None,
) -> dict:
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY. Define it in the .env file.")

    payload = {
        "model": model_override or get_groq_model(),
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres OpenClaw, un asistente transaccional para CREAR hipótesis y records. "
                    "Trabajas únicamente en borradores estructurados. Responde SOLO con JSON válido. "
                    "Nunca confirmes creación ni ejecutes acciones. No uses markdown. No hagas análisis "
                    "de negocio ni respuestas largas. Si falta información, deja el campo en null. "
                    "Optimiza tus borradores para marketing, copywriting, lean startup y publicidad "
                    "(desde enfoques científicos hasta persuasivos), apoyándote en psicología y sociología. "
                    "Usa el contexto entregado (incluyendo hipótesis y records recientes con resultados) "
                    "para inferir y proponer mejores borradores, sin mezclarte con otros asistentes. "
                    "Devuelve un objeto con las claves: draft, notes. "
                    "El campo draft debe ser un objeto con las claves disponibles del tipo solicitado. "
                    "Para hipótesis siempre incluye metric_x (resumen de 3-4 palabras del CAMBIO/ACCIÓN "
                    "que se ejecuta, ej: \"hook indiferencia\", NO del resultado), "
                    "primary_metric, threshold_operator, threshold_value, threshold_type, "
                    "volume_min_value y volume_unit. "
                    "Nunca omitas hypothesis_type en hipótesis; el JSON debe venir completo. "
                    "No incluyas campos de records en hipótesis (ej: hook_type, cta_type, execution_type). "
                    "Para records, siempre incluye project_name y metric_x para enlazar con la hipótesis "
                    "y recuerda que un record es una prueba que recolecta evidencia."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "draft_type": draft_type,
                        "message": message,
                        "existing_draft": existing_draft or {},
                        "context": context,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }

    try:
        resp = requests.post(
            get_groq_api_url(),
            json=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            timeout=45,
        )
    except requests.ConnectionError as exc:
        raise GroqError(f"Groq connection error: {exc}") from exc
    except requests.Timeout as exc:
        raise GroqError("Groq request timed out.") from exc
    except Exception as exc:
        raise GroqError(f"Groq request failed: {exc}") from exc

    if resp.status_code != 200:
        error_body = resp.text
        error_message = _extract_error_message(error_body)
        if resp.status_code == 402:
            raise GroqError(
                "Groq sin saldo. Agrega creditos o actualiza la API key.",
                status_code=402,
            )
        if error_message:
            raise GroqError(f"Groq error: {error_message}")
        raise GroqError(f"Groq HTTP error {resp.status_code}: {error_body}")

    body = resp.text

    try:
        response_data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise GroqError("Groq returned invalid JSON.") from exc

    content = (
        response_data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        raise GroqError("Groq response missing content.")

    try:
        draft_response = json.loads(content)
    except json.JSONDecodeError as exc:
        draft_response = _extract_json_from_text(content)
        if draft_response is None:
            raise GroqError("Groq draft response was not JSON.") from exc

    if not isinstance(draft_response, dict) or "draft" not in draft_response:
        raise GroqError("Groq draft response missing draft payload.")
    return draft_response


def _extract_json_from_text(content: str) -> dict | None:
    """Extract the first JSON object from a text response."""
    start = content.find("{")
    if start == -1:
        return None
    depth = 0
    for idx in range(start, len(content)):
        char = content[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                candidate = content[start : idx + 1]
                try:
                    payload = json.loads(candidate)
                except json.JSONDecodeError:
                    return None
                if isinstance(payload, dict):
                    return payload
                return None
    return None


# ------------------------------------------------------------------ #
#  PROMPT VERSIONS
# ------------------------------------------------------------------ #
METRICS_PROMPT_VERSION = "v1.0"
NOTES_PROMPT_VERSION = "v1.0"
COMBINED_PROMPT_VERSION = "v1.0"


# ------------------------------------------------------------------ #
#  IA MÉTRICAS — Only quantitative data
# ------------------------------------------------------------------ #

def _build_metrics_input(
    experiment: Experiment,
    evaluation: ExperimentEvaluation,
    records: list[ExperimentRecord],
) -> dict:
    """Build input snapshot for metrics analysis. NO qualitative data."""
    volume_actual = evaluation.total_volume
    volume_min = experiment.volume_min_value
    volume_insufficient = bool(volume_min and volume_actual < volume_min)

    records_summary = []
    for r in records:
        rec_data: dict = {
            "record_id": r.id,
            "execution_type": r.execution_type,
            "record_status": r.record_status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        metrics_fields = [
            "clicks", "views", "likes", "comments", "shares", "saves",
            "views_finish_pct", "retention_pct", "avg_watch_time", "video_duration",
            "ctr", "cpc", "initiate_checkouts", "view_content", "lead_form", "purchase",
            "paid_video_duration", "live_viewers_peak", "live_avg_viewers",
            "live_duration", "live_new_followers",
        ]
        rec_metrics = {}
        for field in metrics_fields:
            value = getattr(r, field, None)
            if value is not None:
                rec_metrics[field] = value
        if rec_metrics:
            rec_data["metrics"] = rec_metrics
        records_summary.append(rec_data)

    # Compute simple variance flag
    if records and experiment.primary_metric:
        values = []
        for r in records:
            v = getattr(r, experiment.primary_metric, None)
            if v is not None:
                values.append(float(v))
        if len(values) >= 2:
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            high_variance = variance > (mean * 0.5) ** 2 if mean != 0 else variance > 0
        else:
            high_variance = False
    else:
        high_variance = False

    return {
        "experiment": {
            "id": experiment.id,
            "project_name": experiment.project_name,
            "hypothesis": experiment.hypothesis,
            "hypothesis_type": experiment.hypothesis_type,
            "traffic_type": experiment.traffic_type,
            "primary_metric": experiment.primary_metric,
            "threshold_operator": experiment.threshold_operator,
            "threshold_value": experiment.threshold_value,
            "threshold_type": experiment.threshold_type,
            "volume_unit": experiment.volume_unit,
            "volume_min_value": experiment.volume_min_value,
            "experiment_status": experiment.experiment_status,
        },
        "evaluation": {
            "aggregated_value": evaluation.aggregated_value,
            "total_volume": evaluation.total_volume,
            "volume_sufficient": evaluation.volume_sufficient,
            "all_records_closed": evaluation.all_records_closed,
            "ready_to_evaluate": evaluation.ready_to_evaluate,
            "suggested_status": evaluation.suggested_status,
            "records_collecting": evaluation.records_collecting,
            "records_closed": evaluation.records_closed,
            "segmented_by_public": evaluation.segmented_by_public,
            "segments": [
                {
                    "publico": segment.publico,
                    "records_total": segment.records_total,
                    "aggregated_value": segment.aggregated_value,
                    "comparison_value": segment.comparison_value,
                    "total_volume": segment.total_volume,
                    "volume_sufficient": segment.volume_sufficient,
                    "all_records_closed": segment.all_records_closed,
                    "ready_to_evaluate": segment.ready_to_evaluate,
                    "suggested_status": segment.suggested_status,
                    "explanation": segment.explanation,
                }
                for segment in evaluation.segments
            ],
        },
        "flags": {
            "volume_insufficient": volume_insufficient,
            "high_variance": high_variance,
        },
        "records_count": len(records),
        "records": records_summary,
    }


_METRICS_SYSTEM_PROMPT = (
    "Eres un mentor Lean Startup y analista cuantitativo senior. "
    "Analiza EXCLUSIVAMENTE los datos cuantitativos (métricas, umbrales, volumen, estados, records) "
    "del experimento proporcionado. "
    "NO asumas ni uses información cualitativa, notas ni documentación. "
    "Responde SIEMPRE en español.\n\n"
    "Tu output DEBE seguir esta estructura:\n"
    "1. **Fuente usada: Métricas**\n"
    "2. **Estado actual**: estado del experimento según métricas + explicación breve\n"
    "3. **Riesgos de datos**: volumen insuficiente, varianza alta, sesgo de canal, etc.\n"
    "4. **Recomendaciones accionables** (máximo 5): qué hacer ahora, próximo ciclo, qué cambiar\n"
    "5. **Hipótesis próxima recomendada**: 1 hipótesis concreta basada en datos\n"
    "6. **Checklist de decisión**: Escalar / Pivotar / Invalidar (con justificación cuantitativa)\n\n"
    "IMPORTANTE: Al final incluye la línea: 'No asumí documentación cualitativa.'"
)


def generate_metrics_analysis(
    experiment: Experiment,
    evaluation: ExperimentEvaluation,
    records: list[ExperimentRecord],
) -> tuple[str, str]:
    """Generate metrics-only AI analysis. Returns (output_text, input_snapshot_json)."""
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY. Define it in the .env file.")

    input_data = _build_metrics_input(experiment, evaluation, records)
    input_snapshot = json.dumps(input_data, ensure_ascii=False, indent=2)

    payload = {
        "model": get_groq_model(),
        "messages": [
            {"role": "system", "content": _METRICS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Analiza las métricas cuantitativas del siguiente experimento. "
                    "Usa SOLO los datos proporcionados:\n"
                    f"{input_snapshot}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
    }

    content = _call_groq(payload)
    return content, input_snapshot


# ------------------------------------------------------------------ #
#  IA NOTAS — Only qualitative documentation
# ------------------------------------------------------------------ #

def _build_notes_input(
    entity_type: str,
    entity_id: int,
    documentation: Documentation | None,
) -> dict:
    """Build input snapshot for notes analysis. NO metrics."""
    notes_data = []
    if documentation and documentation.notes:
        for note in documentation.notes:
            notes_data.append({
                "note_id": note.id,
                "body": note.body,
                "created_at": note.created_at.isoformat() if note.created_at else None,
                "updated_at": note.updated_at.isoformat() if note.updated_at else None,
            })

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "notes_count": len(notes_data),
        "notes": notes_data,
    }


def _build_ai_history_snapshot(analyses: list[AIAnalysis]) -> list[dict]:
    history = []
    for analysis in analyses:
        history.append({
            "analysis_id": analysis.id,
            "analysis_type": analysis.analysis_type,
            "model": analysis.model,
            "prompt_version": analysis.prompt_version,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
            "output": analysis.output,
        })
    return history


_NOTES_SYSTEM_PROMPT = (
    "Eres un analista cualitativo senior y experto en documentación de experimentos. "
    "Analiza EXCLUSIVAMENTE la documentación cualitativa (contexto inicial y notas) "
    "de la entidad proporcionada. "
    "NO uses ni asumas métricas cuantitativas, umbrales ni volúmenes. "
    "Responde SIEMPRE en español.\n\n"
    "Tu output DEBE seguir esta estructura:\n"
    "1. **Fuente usada: Documentación**\n"
    "2. **Síntesis**: qué se intentó, por qué, qué se observó cualitativamente\n"
    "3. **Patrones en notas**: objeciones recurrentes, temas frecuentes\n"
    "4. **Dudas abiertas**: preguntas sin resolver detectadas en la documentación\n"
    "5. **Recomendaciones de documentación**: qué falta documentar, lagunas detectadas\n"
    "6. **Formato recomendado**: sugerencia de estructura para notas futuras\n"
    "7. **Decisiones sugeridas**: desde lo cualitativo, sin datos cuantitativos\n\n"
    "IMPORTANTE: Al final incluye la línea: 'No usé métricas cuantitativas.'"
)


def generate_notes_analysis(
    entity_type: str,
    entity_id: int,
    documentation: Documentation | None,
) -> tuple[str, str]:
    """Generate notes-only AI analysis. Returns (output_text, input_snapshot_json)."""
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY. Define it in the .env file.")

    input_data = _build_notes_input(entity_type, entity_id, documentation)
    input_snapshot = json.dumps(input_data, ensure_ascii=False, indent=2)

    payload = {
        "model": get_groq_model(),
        "messages": [
            {"role": "system", "content": _NOTES_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Analiza la documentación cualitativa de la siguiente entidad. "
                    "Usa SOLO las notas proporcionadas:\n"
                    f"{input_snapshot}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 1200,
    }

    content = _call_groq(payload)
    return content, input_snapshot


# ------------------------------------------------------------------ #
#  IA COMBINADA — Metrics + Documentation + AI history
# ------------------------------------------------------------------ #

def _build_combined_input(
    experiment: Experiment,
    evaluation: ExperimentEvaluation,
    records: list[ExperimentRecord],
    focus_record: ExperimentRecord | None,
    experiment_doc: Documentation | None,
    record_doc: Documentation | None,
    experiment_ai_history: list[AIAnalysis],
    record_ai_history: list[AIAnalysis],
) -> dict:
    exp_metrics = _build_metrics_input(experiment, evaluation, records)
    combined = {
        "experiment": exp_metrics.get("experiment", {}),
        "evaluation": exp_metrics.get("evaluation", {}),
        "flags": exp_metrics.get("flags", {}),
        "records_count": exp_metrics.get("records_count", 0),
        "records": exp_metrics.get("records", []),
        "focus_record": _record_to_payload(focus_record) if focus_record else None,
        "documentation": {
            "experiment": _build_notes_input("experiment", experiment.id, experiment_doc),
            "record": _build_notes_input("record", focus_record.id, record_doc) if focus_record else None,
        },
        "ai_history": {
            "experiment": _build_ai_history_snapshot(experiment_ai_history),
            "record": _build_ai_history_snapshot(record_ai_history) if focus_record else [],
        },
    }
    return combined


_COMBINED_SYSTEM_PROMPT = (
    "Eres un estratega senior de experimentos y analista integral. "
    "Analiza EN CONJUNTO métricas cuantitativas, documentación cualitativa "
    "y el historial de análisis IA disponibles. "
    "Integra el contexto de la hipótesis y explica cómo se alinea o no con el record. "
    "Responde SIEMPRE en español.\n\n"
    "Tu output DEBE seguir esta estructura:\n"
    "1. **Fuente usada: Métricas + Documentación + Historial IA**\n"
    "2. **Resumen integral**: visión general del experimento y el record (si aplica)\n"
    "3. **Hallazgos alineados record ↔ hipótesis**: qué valida o contradice la hipótesis\n"
    "4. **Tensiones o contradicciones**: discrepancias entre métricas y notas\n"
    "5. **Recomendaciones accionables** (máximo 6): decisiones alineadas record/hipótesis\n"
    "6. **Siguientes pasos + documentación**: qué medir, qué documentar y por qué\n\n"
    "IMPORTANTE: Si falta información, indica explícitamente qué falta."
)


def generate_combined_analysis(
    experiment: Experiment,
    evaluation: ExperimentEvaluation,
    records: list[ExperimentRecord],
    focus_record: ExperimentRecord | None,
    experiment_doc: Documentation | None,
    record_doc: Documentation | None,
    experiment_ai_history: list[AIAnalysis],
    record_ai_history: list[AIAnalysis],
) -> tuple[str, str]:
    """Generate combined AI analysis. Returns (output_text, input_snapshot_json)."""
    api_key = get_groq_api_key()
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY. Define it in the .env file.")

    input_data = _build_combined_input(
        experiment=experiment,
        evaluation=evaluation,
        records=records,
        focus_record=focus_record,
        experiment_doc=experiment_doc,
        record_doc=record_doc,
        experiment_ai_history=experiment_ai_history,
        record_ai_history=record_ai_history,
    )
    input_snapshot = json.dumps(input_data, ensure_ascii=False, indent=2)

    payload = {
        "model": get_groq_model(),
        "messages": [
            {"role": "system", "content": _COMBINED_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Entrega un análisis integral basado en el siguiente contexto JSON:\n"
                    f"{input_snapshot}"
                ),
            },
        ],
        "temperature": 0.2,
        "max_tokens": 1400,
    }

    content = _call_groq(payload)
    return content, input_snapshot


# ------------------------------------------------------------------ #
#  Shared Groq caller
# ------------------------------------------------------------------ #

def _call_groq(payload: dict) -> str:
    """Call Groq API and return content string."""
    api_key = get_groq_api_key()
    try:
        resp = requests.post(
            get_groq_api_url(),
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=45,
        )
    except requests.ConnectionError as exc:
        raise GroqError(f"Groq connection error: {exc}") from exc
    except requests.Timeout as exc:
        raise GroqError("Groq request timed out.") from exc
    except Exception as exc:
        raise GroqError(f"Groq request failed: {exc}") from exc

    if resp.status_code != 200:
        error_body = resp.text
        error_message = _extract_error_message(error_body)
        if resp.status_code == 402:
            raise GroqError(
                "Groq sin saldo. Agrega creditos o actualiza la API key.",
                status_code=402,
            )
        if error_message:
            raise GroqError(f"Groq error: {error_message}")
        raise GroqError(f"Groq HTTP error {resp.status_code}: {error_body}")

    try:
        response_data = json.loads(resp.text)
    except json.JSONDecodeError as exc:
        raise GroqError("Groq returned invalid JSON.") from exc

    content = (
        response_data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        raise GroqError("Groq response missing content.")
    return str(content).strip()
