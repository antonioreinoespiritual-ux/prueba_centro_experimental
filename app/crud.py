# app/crud.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

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

    db.commit()
    db.refresh(exp)
    return exp


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
        hook_text=hook_text,
        hook_type=data.hook_type,
        cta_text=cta_text,
        cta_type=data.cta_type,
        creative_id=creative_id,
        record_status="collecting",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
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
    db.commit()
    db.refresh(rec)
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
#  HYPOTHESIS EVALUATION
# ------------------------------------------------------------------ #

def _compute_aggregated_metric(records: list[models.ExperimentRecord], metric: str) -> tuple[float | None, int]:
    """Compute an aggregated metric across all records.

    For rate metrics (ending in _rate): compute as sum(numerator)/sum(denominator).
    For direct metrics: sum all values.

    Returns (aggregated_value, total_volume).
    """
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
        total_num = 0
        total_den = 0
        for r in records:
            n = getattr(r, num_field, None) or 0
            d = getattr(r, den_field, None) or 0
            total_num += n
            total_den += d
        if total_den == 0:
            return None, 0
        return (total_num / total_den) * 100, total_den

    # Direct sum metrics
    if metric == "cpc":
        total = 0.0
        count = 0
        for r in records:
            v = getattr(r, "cpc", None)
            if v is not None:
                total += v
                count += 1
        if count == 0:
            return None, 0
        return total / count, count

    # Averaged metrics (percentages, time)
    averaged_metrics = {"views_finish_pct", "retention_pct", "avg_watch_time"}
    if metric in averaged_metrics:
        total = 0.0
        count = 0
        for r in records:
            v = getattr(r, metric, None)
            if v is not None:
                total += v
                count += 1
        if count == 0:
            return None, 0
        return total / count, count

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


def _compute_volume_total(records: list[models.ExperimentRecord], volume_unit: str | None) -> int:
    if not volume_unit:
        return 0
    volume_field_map = {
        "ctr": "views",
        "cpc": "clicks",
        "initiate_checkout_rate": "views",
        "view_content_rate": "views",
        "lead_rate": "views",
        "purchase_rate": "views",
        "views": "views",
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
    if ready and aggregated_value is not None:
        op = exp.threshold_operator
        threshold_val = exp.threshold_value
        threshold_type = exp.threshold_type
        if op and threshold_val is not None and threshold_type:
            if op == ">=" and aggregated_value >= threshold_val:
                suggested_status = "validated"
            elif op == ">" and aggregated_value > threshold_val:
                suggested_status = "validated"
            elif op == "<=" and aggregated_value <= threshold_val:
                suggested_status = "validated"
            elif op == "<" and aggregated_value < threshold_val:
                suggested_status = "validated"
            else:
                suggested_status = "invalidated"

    return schemas.ExperimentEvaluation(
        experiment_id=experiment_id,
        primary_metric=exp.primary_metric,
        aggregated_value=round(aggregated_value, 4) if aggregated_value is not None else None,
        threshold_raw=exp.validation_threshold,
        threshold_value=exp.threshold_value,
        threshold_type=exp.threshold_type,
        threshold_operator=exp.threshold_operator,
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
