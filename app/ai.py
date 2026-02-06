from __future__ import annotations

import json

import requests

from .config import get_groq_api_key, get_groq_api_url, get_groq_model
from .models import Experiment, ExperimentRecord
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
