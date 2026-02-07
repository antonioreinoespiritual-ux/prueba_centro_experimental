# app/routers/documentation.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
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


@router.get("/{entity_type}/{entity_id}", response_model=schemas.DocumentationOut)
def get_documentation(
    entity_type: schemas.EntityType,
    entity_id: int,
    db: Session = Depends(get_db),
):
    doc = crud.get_documentation(db, entity_type, entity_id)
    if not doc:
        # Auto-create empty documentation on first access
        doc = crud.get_or_create_documentation(db, entity_type, entity_id)
    return doc


@router.post("/{entity_type}/{entity_id}/notes", response_model=schemas.DocumentationNoteOut)
def create_note(
    entity_type: schemas.EntityType,
    entity_id: int,
    data: schemas.DocumentationNoteCreate,
    db: Session = Depends(get_db),
):
    note = crud.create_documentation_note(db, entity_type, entity_id, data.body)
    return note


@router.patch("/notes/{note_id}", response_model=schemas.DocumentationNoteOut)
def update_note(
    note_id: int,
    data: schemas.DocumentationNoteUpdate,
    db: Session = Depends(get_db),
):
    note = crud.update_documentation_note(db, note_id, data.body)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note
