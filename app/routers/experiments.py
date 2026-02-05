# app/routers/experiments.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.ExperimentOut)
def create_experiment(experiment: schemas.ExperimentCreate, db: Session = Depends(get_db)):
    return crud.create_experiment(db, experiment)


@router.get("/", response_model=list[schemas.ExperimentOut])
def list_experiments(db: Session = Depends(get_db)):
    return crud.get_experiments(db)
