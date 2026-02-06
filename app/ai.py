from __future__ import annotations

import json
import urllib.error
import urllib.request

from .config import get_deepseek_api_key, get_deepseek_api_url, get_deepseek_model
from .models import Experiment, ExperimentRecord
from .schemas import ExperimentEvaluation


class DeepSeekError(RuntimeError):
    pass


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
    api_key = get_deepseek_api_key()
    if not api_key:
        raise ValueError("Missing DEEPSEEK_API_KEY. Define it in the .env file.")

    payload = {
        "model": get_deepseek_model(),
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un analista senior de experimentos. Entrega un analisis completo en español "
                    "usando los datos disponibles. Incluye resumen ejecutivo, hallazgos clave, "
                    "riesgos, recomendaciones accionables y siguientes pasos."
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

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        get_deepseek_api_url(),
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8") if exc.fp else ""
        raise DeepSeekError(f"DeepSeek HTTP error {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise DeepSeekError(f"DeepSeek connection error: {exc.reason}") from exc
    except Exception as exc:
        raise DeepSeekError(f"DeepSeek request failed: {exc}") from exc

    try:
        response_data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DeepSeekError("DeepSeek returned invalid JSON.") from exc

    content = (
        response_data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
    )
    if not content:
        raise DeepSeekError("DeepSeek response missing content.")
    return str(content).strip()
