from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter(prefix="/clients", tags=["clients"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[schemas.ClientOut])
def list_clients(
    search: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.list_clients(db, search=search, country=country, limit=limit, offset=offset)


@router.post("", response_model=schemas.ClientOut)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    return crud.create_client(db, payload)


@router.get("/{client_id}", response_model=schemas.ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    item = crud.get_client(db, client_id)
    if not item:
        raise HTTPException(status_code=404, detail="Client not found")
    return item


@router.patch("/{client_id}", response_model=schemas.ClientOut)
def update_client(client_id: int, payload: schemas.ClientUpdate, db: Session = Depends(get_db)):
    item = crud.update_client(db, client_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Client not found")
    return item


@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    result = crud.delete_client(db, client_id)
    if not result:
        raise HTTPException(status_code=404, detail="Client not found")
    return result


@router.get("/{client_id}/interviews", response_model=list[schemas.InterviewSessionOut])
def list_client_interviews(client_id: int, db: Session = Depends(get_db)):
    return crud.list_client_interviews(db, client_id)
