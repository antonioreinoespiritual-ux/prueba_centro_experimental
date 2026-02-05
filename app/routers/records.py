# app/routers/records.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import schemas, crud
from ..database import SessionLocal

router = APIRouter()


def get_db():
  db = SessionLocal()
  try:
      yield db
  finally:
      db.close()


@router.post("/", response_model=schemas.RecordOut)
def create_record(
    record: schemas.RecordCreate,
    db: Session = Depends(get_db),
):
    return crud.create_record(db, record)


@router.get("/", response_model=list[schemas.RecordOut])
def list_records(
    experiment_id: int | None = Query(default=None),
    limit: int = Query(default=5000, ge=1, le=50000),
    db: Session = Depends(get_db),
):
    return crud.get_records(db, experiment_id=experiment_id, limit=limit)
