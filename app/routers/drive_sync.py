from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..services import drive_sync_service

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/api/drive-sync/bootstrap")
def bootstrap():
    return {"folders": drive_sync_service.bootstrap_base()}


@router.post("/api/drive-sync/backfill")
def backfill(db: Session = Depends(get_db)):
    return drive_sync_service.backfill_all(db)


@router.post("/api/drive-sync/hypotheses/{experiment_id}")
def sync_hypothesis(experiment_id: int, db: Session = Depends(get_db)):
    exp = drive_sync_service.sync_hypothesis(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return {"id": exp.id, "drive_folder_path": exp.drive_folder_path}


@router.post("/api/drive-sync/records/{record_id}")
def sync_record(record_id: int, db: Session = Depends(get_db)):
    record = drive_sync_service.sync_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"id": record.id, "drive_folder_path": record.drive_folder_path}


@router.post("/api/drive-sync/consolidate")
def consolidate_duplicates(db: Session = Depends(get_db)):
    return drive_sync_service.consolidate_duplicates(db)
