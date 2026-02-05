# app/crud.py
from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from . import models, schemas


def create_experiment(db: Session, data: schemas.ExperimentCreate):
    obj = models.Experiment(
        project_name=data.project_name,
        hypothesis=data.hypothesis,
        traffic_type=data.traffic_type,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_experiments(db: Session):
    q = select(models.Experiment).order_by(desc(models.Experiment.created_at))
    return list(db.execute(q).scalars().all())


def create_record(db: Session, data: schemas.RecordCreate):
    # Normalización: si viene string vacío => None (por seguridad)
    organic_piece_type = (data.organic_piece_type or "").strip() or None

    obj = models.ExperimentRecord(
        experiment_id=data.experiment_id,
        session_id=data.session_id,

        clicks=data.clicks,
        views=data.views,

        organic_piece_type=organic_piece_type,
        likes=data.likes,
        comments=data.comments,
        shares=data.shares,
        saves=data.saves,

        ctr=data.ctr,
        cpc=data.cpc,
        initiate_checkouts=data.initiate_checkouts,
        view_content=data.view_content,
        lead_form=data.lead_form,
        purchase=data.purchase,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_records(
    db: Session,
    experiment_id: int | None = None,
    limit: int = 5000,
):
    q = select(models.ExperimentRecord).order_by(desc(models.ExperimentRecord.created_at)).limit(limit)
    if experiment_id:
        q = q.where(models.ExperimentRecord.experiment_id == experiment_id)
    return list(db.execute(q).scalars().all())
