# app/crud.py
from __future__ import annotations

from datetime import datetime
import re

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, delete, update

from . import models, schemas


# ------------------------------------------------------------------ #
#  EXPERIMENTS
# ------------------------------------------------------------------ #

def create_experiment(db: Session, data: schemas.ExperimentCreate):
    obj = models.Experiment(
        project_name=data.project_name,
        hypothesis=data.hypothesis,
        traffic_type=data.traffic_type,
        hypothesis_type=data.hypothesis_type,
        independent_variable=(data.independent_variable or "").strip() or None,
        primary_metric=data.primary_metric,
        validation_threshold=(data.validation_threshold or "").strip() or None,
        threshold_value=data.threshold_value,
        threshold_type=data.threshold_type,
        threshold_operator=data.threshold_operator,
        experiment_status=data.experiment_status or "draft",
        min_volume=data.min_volume,
        volume_min_value=data.volume_min_value,
        volume_unit=data.volume_unit,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)

    # Auto-create documentation with initial note if contexto is provided
    contexto = (getattr(data, "contexto", None) or "").strip()
    if contexto:
        create_documentation_note(db, "experiment", obj.id, contexto)

    return obj


def get_experiments(db: Session):
    q = select(models.Experiment).order_by(desc(models.Experiment.created_at))
    return list(db.execute(q).scalars().all())


def get_experiment(db: Session, experiment_id: int):
    q = select(models.Experiment).where(models.Experiment.id == experiment_id)
    return db.execute(q).scalar_one_or_none()


def update_experiment(db: Session, experiment_id: int, data: schemas.ExperimentUpdate):
    exp = get_experiment(db, experiment_id)
    if not exp:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(exp, field, value)
    exp.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(exp)
    return exp


def delete_experiment(db: Session, experiment_id: int):
    exp = get_experiment(db, experiment_id)
    if not exp:
        return None

    record_ids = [record.id for record in exp.records]
    if record_ids:
        db.execute(
            delete(models.Documentation).where(
                models.Documentation.entity_type == "record",
                models.Documentation.entity_id.in_(record_ids),
            )
        )
        db.execute(
            delete(models.AIAnalysis).where(
                models.AIAnalysis.entity_type == "record",
                models.AIAnalysis.entity_id.in_(record_ids),
            )
        )

    db.execute(
        delete(models.Documentation).where(
            models.Documentation.entity_type == "experiment",
            models.Documentation.entity_id == experiment_id,
        )
    )
    db.execute(
        delete(models.AIAnalysis).where(
            models.AIAnalysis.entity_type == "experiment",
            models.AIAnalysis.entity_id == experiment_id,
        )
    )
    db.delete(exp)
    db.commit()
    return exp


def delete_project(db: Session, project_name: str):
    exp_ids = list(
        db.execute(
            select(models.Experiment.id).where(models.Experiment.project_name == project_name)
        ).scalars()
    )
    if not exp_ids:
        return 0

    record_ids = list(
        db.execute(
            select(models.ExperimentRecord.id).where(
                models.ExperimentRecord.experiment_id.in_(exp_ids)
            )
        ).scalars()
    )

    if record_ids:
        db.execute(
            delete(models.Documentation).where(
                models.Documentation.entity_type == "record",
                models.Documentation.entity_id.in_(record_ids),
            )
        )
        db.execute(
            delete(models.AIAnalysis).where(
                models.AIAnalysis.entity_type == "record",
                models.AIAnalysis.entity_id.in_(record_ids),
            )
        )
        db.execute(
            delete(models.ExperimentRecord).where(
                models.ExperimentRecord.id.in_(record_ids)
            )
        )

    db.execute(
        delete(models.Documentation).where(
            models.Documentation.entity_type == "experiment",
            models.Documentation.entity_id.in_(exp_ids),
        )
    )
    db.execute(
        delete(models.AIAnalysis).where(
            models.AIAnalysis.entity_type == "experiment",
            models.AIAnalysis.entity_id.in_(exp_ids),
        )
    )
    db.execute(delete(models.Experiment).where(models.Experiment.id.in_(exp_ids)))
    db.commit()
    return len(exp_ids)


def rename_project(db: Session, project_name: str, new_project_name: str):
    result = db.execute(
        update(models.Experiment)
        .where(models.Experiment.project_name == project_name)
        .values(project_name=new_project_name, updated_at=datetime.utcnow())
    )
    db.commit()
    return result.rowcount or 0


# ------------------------------------------------------------------ #
#  RECORDS
# ------------------------------------------------------------------ #

def create_record(db: Session, data: schemas.RecordCreate):
    # Normalización: si viene string vacío => None (por seguridad)
    organic_piece_type = (data.organic_piece_type or "").strip() or None
    video_url = (data.video_url or "").strip() or None
    campaign_id = (data.campaign_id or "").strip() or None
    ad_set_id = (data.ad_set_id or "").strip() or None
    ad_id = (data.ad_id or "").strip() or None
    hook_text = (data.hook_text or "").strip() or None
    cta_text = (data.cta_text or "").strip() or None
    creative_id = (data.creative_id or "").strip() or None

    obj = models.ExperimentRecord(
        experiment_id=data.experiment_id,
        session_id=data.session_id,

        clicks=data.clicks,
        views=data.views,
        views_profile=data.views_profile,
        inicia_test=data.inicia_test,

        # orgánico
        organic_piece_type=organic_piece_type,
        likes=data.likes,
        comments=data.comments,
        shares=data.shares,
        saves=data.saves,

        # orgánico - video metrics
        video_url=video_url,
        views_finish_pct=data.views_finish_pct,
        retention_pct=data.retention_pct,
        avg_watch_time=data.avg_watch_time,
        video_duration=data.video_duration,

        # paid
        ctr=data.ctr,
        cpc=data.cpc,
        initiate_checkouts=data.initiate_checkouts,
        view_content=data.view_content,
        lead_form=data.lead_form,
        purchase=data.purchase,

        # paid - video and campaign metrics
        paid_video_duration=data.paid_video_duration,
        campaign_id=campaign_id,
        ad_set_id=ad_set_id,
        ad_id=ad_id,

        # live metrics
        live_viewers_peak=data.live_viewers_peak,
        live_avg_viewers=data.live_avg_viewers,
        live_duration=data.live_duration,
        live_new_followers=data.live_new_followers,

        # creative / execution
        execution_type=data.execution_type,
        record_name=(data.record_name or "").strip() or None,
        hook_text=hook_text,
        hook_type=data.hook_type,
        cta_text=cta_text,
        cta_type=data.cta_type,
        creative_id=creative_id,
        record_status="collecting",
    )
    obj.updated_at = datetime.utcnow()
    exp = get_experiment(db, data.experiment_id)
    if exp:
        exp.updated_at = datetime.utcnow()
    db.add(obj)
    db.commit()
    db.refresh(obj)

    # Auto-create documentation with initial note if contexto_record is provided
    contexto_record = (getattr(data, "contexto_record", None) or "").strip()
    if contexto_record:
        create_documentation_note(db, "record", obj.id, contexto_record)

    return obj


def get_record(db: Session, record_id: int):
    q = select(models.ExperimentRecord).where(models.ExperimentRecord.id == record_id)
    return db.execute(q).scalar_one_or_none()


def update_record(db: Session, record_id: int, data: schemas.RecordUpdate):
    """Update metrics on an existing record. Does NOT create a new record."""
    rec = get_record(db, record_id)
    if not rec:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(rec, field, value)

    rec.updated_at = datetime.utcnow()
    exp = get_experiment(db, rec.experiment_id)
    if exp:
        exp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return rec


def close_record(db: Session, record_id: int):
    """Mark a record as closed (no longer receiving traffic)."""
    rec = get_record(db, record_id)
    if not rec:
        return None
    rec.record_status = "closed"
    rec.updated_at = datetime.utcnow()
    exp = get_experiment(db, rec.experiment_id)
    if exp:
        exp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return rec


def reopen_record(db: Session, record_id: int):
    """Reopen a closed record (back to collecting)."""
    rec = get_record(db, record_id)
    if not rec:
        return None
    rec.record_status = "collecting"
    rec.updated_at = datetime.utcnow()
    exp = get_experiment(db, rec.experiment_id)
    if exp:
        exp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return rec


def delete_record(db: Session, record_id: int):
    rec = get_record(db, record_id)
    if not rec:
        return None
    db.execute(
        delete(models.Documentation).where(
            models.Documentation.entity_type == "record",
            models.Documentation.entity_id == record_id,
        )
    )
    db.execute(
        delete(models.AIAnalysis).where(
            models.AIAnalysis.entity_type == "record",
            models.AIAnalysis.entity_id == record_id,
        )
    )
    db.delete(rec)
    db.commit()
    return rec


def get_records(
    db: Session,
    experiment_id: int | None = None,
    limit: int = 5000,
):
    q = select(models.ExperimentRecord).order_by(desc(models.ExperimentRecord.created_at)).limit(limit)
    if experiment_id:
        q = q.where(models.ExperimentRecord.experiment_id == experiment_id)
    return list(db.execute(q).scalars().all())


# ------------------------------------------------------------------ #
#  DOCUMENTATION (qualitative, separate from metrics)
# ------------------------------------------------------------------ #

def get_or_create_documentation(db: Session, entity_type: str, entity_id: int) -> models.Documentation:
    q = select(models.Documentation).where(
        models.Documentation.entity_type == entity_type,
        models.Documentation.entity_id == entity_id,
    )
    doc = db.execute(q).scalar_one_or_none()
    if doc:
        return doc
    doc = models.Documentation(entity_type=entity_type, entity_id=entity_id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def get_documentation(db: Session, entity_type: str, entity_id: int):
    q = select(models.Documentation).where(
        models.Documentation.entity_type == entity_type,
        models.Documentation.entity_id == entity_id,
    )
    return db.execute(q).scalar_one_or_none()


def create_documentation_note(db: Session, entity_type: str, entity_id: int, body: str) -> models.DocumentationNote:
    doc = get_or_create_documentation(db, entity_type, entity_id)
    note = models.DocumentationNote(documentation_id=doc.id, body=body)
    db.add(note)
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    db.refresh(doc)
    return note


def update_documentation_note(db: Session, note_id: int, body: str):
    q = select(models.DocumentationNote).where(models.DocumentationNote.id == note_id)
    note = db.execute(q).scalar_one_or_none()
    if not note:
        return None
    note.body = body
    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note


# ------------------------------------------------------------------ #
#  AI ANALYSIS
# ------------------------------------------------------------------ #

def create_ai_analysis(
    db: Session,
    entity_type: str,
    entity_id: int,
    analysis_type: str,
    model: str,
    prompt_version: str,
    input_snapshot: str,
    output: str,
) -> models.AIAnalysis:
    obj = models.AIAnalysis(
        entity_type=entity_type,
        entity_id=entity_id,
        analysis_type=analysis_type,
        model=model,
        prompt_version=prompt_version,
        input_snapshot=input_snapshot,
        output=output,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_ai_analyses(
    db: Session,
    entity_type: str,
    entity_id: int,
    analysis_type: str | None = None,
) -> list[models.AIAnalysis]:
    q = (
        select(models.AIAnalysis)
        .where(
            models.AIAnalysis.entity_type == entity_type,
            models.AIAnalysis.entity_id == entity_id,
        )
        .order_by(desc(models.AIAnalysis.created_at))
    )
    if analysis_type:
        q = q.where(models.AIAnalysis.analysis_type == analysis_type)
    return list(db.execute(q).scalars().all())


# ------------------------------------------------------------------ #
#  HYPOTHESIS EVALUATION
# ------------------------------------------------------------------ #

def _compute_aggregated_metric(records: list[models.ExperimentRecord], metric: str) -> tuple[float | None, int]:
    """Compute an aggregated metric across all records.

    For rate/percentage metrics: compute a robust aggregate (median) of per-record values.
    For direct count metrics: sum all values.

    Returns (aggregated_value, total_volume).
    """
    def median(values: list[float]) -> float | None:
        if not values:
            return None
        values.sort()
        mid = len(values) // 2
        if len(values) % 2 == 1:
            return values[mid]
        return (values[mid - 1] + values[mid]) / 2

    # Rate metrics require numerator/denominator aggregation
    rate_definitions = {
        "initiate_checkout_rate": ("initiate_checkouts", "views"),
        "view_content_rate": ("view_content", "views"),
        "lead_rate": ("lead_form", "views"),
        "purchase_rate": ("purchase", "views"),
        "ctr": ("clicks", "views"),
    }

    if metric in rate_definitions:
        num_field, den_field = rate_definitions[metric]
        values = []
        for r in records:
            n = getattr(r, num_field, None) or 0
            d = getattr(r, den_field, None) or 0
            if d > 0:
                values.append((n / d) * 100)
        aggregated = median(values)
        if aggregated is None:
            return None, 0
        return aggregated, len(values)

    # Cost metrics: use median to avoid summing across records
    if metric == "cpc":
        values = []
        for r in records:
            v = getattr(r, "cpc", None)
            if v is not None:
                values.append(float(v))
        aggregated = median(values)
        if aggregated is None:
            return None, 0
        return aggregated, len(values)

    # Averaged metrics (percentages, time)
    averaged_metrics = {"views_finish_pct", "retention_pct", "avg_watch_time"}
    if metric in averaged_metrics:
        values = []
        for r in records:
            v = getattr(r, metric, None)
            if v is not None:
                values.append(float(v))
        aggregated = median(values)
        if aggregated is None:
            return None, 0
        return aggregated, len(values)

    # Simple sum metrics
    total = 0
    count = 0
    for r in records:
        v = getattr(r, metric, None)
        if v is not None:
            total += v
            count += 1
    if count == 0:
        return None, 0
    return float(total), count


def _parse_threshold(raw: str | None) -> tuple[str | None, float | None, bool]:
    """Parse threshold like '>= 3%' into (operator, value, is_percent)."""
    if not raw:
        return None, None, False
    raw = raw.strip()
    is_percent = raw.endswith("%")
    raw = raw.rstrip("%").strip()
    match = re.match(r"(>=|<=|>|<|=)\s*([\d.]+)", raw)
    if not match:
        return None, None, is_percent
    return match.group(1), float(match.group(2)), is_percent


def _infer_threshold_type(metric: str | None, is_percent: bool) -> str | None:
    if not metric:
        return "percentage" if is_percent else None
    if is_percent:
        return "percentage"
    if _is_count_metric(metric):
        return "absolute"
    return "decimal"


def _compute_volume_total(records: list[models.ExperimentRecord], volume_unit: str | None) -> int:
    if not volume_unit:
        return 0
    volume_field_map = {
        "clicks": "clicks",
        "ctr": "views",
        "cpc": "clicks",
        "initiate_checkout_rate": "views",
        "view_content_rate": "views",
        "lead_rate": "views",
        "purchase_rate": "views",
        "views": "views",
        "views_profile": "views_profile",
        "inicia_test": "inicia_test",
        "likes": "likes",
        "comments": "comments",
        "shares": "shares",
        "saves": "saves",
        "views_finish_pct": "views",
        "retention_pct": "views",
        "avg_watch_time": "views",
        "live_viewers_peak": "live_viewers_peak",
        "live_avg_viewers": "live_avg_viewers",
        "live_new_followers": "live_new_followers",
    }
    field = volume_field_map.get(volume_unit)
    if not field:
        return 0
    total = 0
    for r in records:
        total += getattr(r, field, None) or 0
    return total


def _is_rate_metric(metric: str) -> bool:
    return metric.endswith("_rate") or metric in {"ctr"}


def _is_percentage_metric(metric: str) -> bool:
    return metric in {"views_finish_pct", "retention_pct"}


def _is_average_metric(metric: str) -> bool:
    return metric in {"avg_watch_time"}


def _is_count_metric(metric: str) -> bool:
    if _is_rate_metric(metric) or _is_percentage_metric(metric) or _is_average_metric(metric):
        return False
    return metric in {
        "clicks",
        "views",
        "views_profile",
        "inicia_test",
        "likes",
        "comments",
        "shares",
        "saves",
        "initiate_checkouts",
        "view_content",
        "lead_form",
        "purchase",
        "live_viewers_peak",
        "live_avg_viewers",
        "live_new_followers",
    }


def evaluate_experiment(db: Session, experiment_id: int) -> schemas.ExperimentEvaluation:
    """Evaluate a hypothesis by aggregating all its records and comparing to threshold."""
    exp = get_experiment(db, experiment_id)
    if not exp:
        return None

    records = get_records(db, experiment_id=experiment_id, limit=50000)

    records_collecting = sum(1 for r in records if r.record_status == "collecting")
    records_closed = sum(1 for r in records if r.record_status == "closed")
    all_closed = records_collecting == 0 and len(records) > 0

    aggregated_value = None

    if exp.primary_metric and records:
        aggregated_value, _ = _compute_aggregated_metric(records, exp.primary_metric)

    volume_total = _compute_volume_total(records, exp.volume_unit)
    min_vol = exp.volume_min_value
    volume_sufficient = bool(min_vol and volume_total >= min_vol)

    ready = volume_sufficient and all_closed

    suggested_status = None
    op = exp.threshold_operator
    threshold_val = exp.threshold_value
    threshold_type = exp.threshold_type
    if (not op or threshold_val is None or not threshold_type) and exp.validation_threshold:
        parsed_op, parsed_val, parsed_percent = _parse_threshold(exp.validation_threshold)
        op = op or parsed_op
        threshold_val = threshold_val if threshold_val is not None else parsed_val
        threshold_type = threshold_type or _infer_threshold_type(exp.primary_metric, parsed_percent)

    if ready and aggregated_value is not None:
        metric = exp.primary_metric
        if op and threshold_val is not None and threshold_type and metric:
            compare_value = None
            if threshold_type == "percentage":
                if _is_rate_metric(metric) or _is_percentage_metric(metric):
                    compare_value = aggregated_value
                elif _is_count_metric(metric):
                    base_total = _compute_volume_total(records, exp.volume_unit)
                    if base_total > 0:
                        compare_value = (aggregated_value / base_total) * 100
            elif threshold_type == "absolute":
                if not _is_rate_metric(metric) and not _is_percentage_metric(metric):
                    compare_value = aggregated_value
            elif threshold_type == "decimal":
                if not _is_rate_metric(metric) and not _is_percentage_metric(metric):
                    compare_value = aggregated_value

            if compare_value is not None:
                if op == ">=" and compare_value >= threshold_val:
                    suggested_status = "validated"
                elif op == ">" and compare_value > threshold_val:
                    suggested_status = "validated"
                elif op == "<=" and compare_value <= threshold_val:
                    suggested_status = "validated"
                elif op == "<" and compare_value < threshold_val:
                    suggested_status = "validated"
                else:
                    suggested_status = "invalidated"

    return schemas.ExperimentEvaluation(
        experiment_id=experiment_id,
        primary_metric=exp.primary_metric,
        aggregated_value=round(aggregated_value, 4) if aggregated_value is not None else None,
        threshold_raw=exp.validation_threshold,
        threshold_value=threshold_val,
        threshold_type=threshold_type,
        threshold_operator=op,
        total_volume=volume_total,
        min_volume=exp.min_volume,
        volume_min_value=exp.volume_min_value,
        volume_unit=exp.volume_unit,
        volume_sufficient=volume_sufficient,
        all_records_closed=all_closed,
        ready_to_evaluate=ready,
        suggested_status=suggested_status,
        records_collecting=records_collecting,
        records_closed=records_closed,
    )
