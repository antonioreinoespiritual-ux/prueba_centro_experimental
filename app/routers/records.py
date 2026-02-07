# app/routers/records.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.get("/{record_id}", response_model=schemas.RecordOut)
def get_record(record_id: int, db: Session = Depends(get_db)):
    rec = crud.get_record(db, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    return rec


@router.patch("/{record_id}", response_model=schemas.RecordOut)
def update_record(
    record_id: int,
    data: schemas.RecordUpdate,
    db: Session = Depends(get_db),
):
    """Update metrics on an existing record. Does NOT create a new record."""
    rec = crud.update_record(db, record_id, data)
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    return rec


@router.post("/{record_id}/close", response_model=schemas.RecordOut)
def close_record(record_id: int, db: Session = Depends(get_db)):
    """Mark a record as closed (frozen metrics)."""
    rec = crud.close_record(db, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    return rec


@router.post("/{record_id}/reopen", response_model=schemas.RecordOut)
def reopen_record(record_id: int, db: Session = Depends(get_db)):
    """Reopen a closed record back to collecting."""
    rec = crud.reopen_record(db, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    return rec


@router.delete("/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    rec = crud.delete_record(db, record_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"deleted": True, "record_id": record_id}
