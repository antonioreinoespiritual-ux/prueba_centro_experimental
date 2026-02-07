# app/routers/publics.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.post("/", response_model=schemas.PublicOut)
def create_public(public: schemas.PublicCreate, db: Session = Depends(get_db)):
    try:
        result = crud.create_public(db, public)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return schemas.PublicOut(
        id=result.id,
        name=result.name,
        description=result.description,
        created_at=result.created_at,
        updated_at=result.updated_at,
        records_count=0,
    )


@router.get("/", response_model=list[schemas.PublicOut])
def list_publics(
    search: str | None = Query(default=None, max_length=200),
    db: Session = Depends(get_db),
):
    rows = crud.get_publics(db, search=search)
    return [
        schemas.PublicOut(
            id=public.id,
            name=public.name,
            description=public.description,
            created_at=public.created_at,
            updated_at=public.updated_at,
            records_count=count,
        )
        for public, count in rows
    ]


@router.get("/{public_id}", response_model=schemas.PublicDetail)
def get_public(public_id: int, db: Session = Depends(get_db)):
    public, records, metrics = crud.get_public_detail(db, public_id)
    if not public:
        raise HTTPException(status_code=404, detail="Public not found")
    return schemas.PublicDetail(
        public=schemas.PublicOut(
            id=public.id,
            name=public.name,
            description=public.description,
            created_at=public.created_at,
            updated_at=public.updated_at,
            records_count=len(records),
        ),
        metrics=metrics,
        records=records,
    )


@router.patch("/{public_id}", response_model=schemas.PublicOut)
def update_public(
    public_id: int,
    data: schemas.PublicUpdate,
    db: Session = Depends(get_db),
):
    try:
        public = crud.update_public(db, public_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not public:
        raise HTTPException(status_code=404, detail="Public not found")
    return schemas.PublicOut(
        id=public.id,
        name=public.name,
        description=public.description,
        created_at=public.created_at,
        updated_at=public.updated_at,
        records_count=len(public.records),
    )
