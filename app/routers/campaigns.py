from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[schemas.ResearchCampaignOut])
def list_campaigns(
    project_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return crud.list_research_campaigns(db, project_id=project_id, status=status, search=search)


@router.get("/{campaign_id}", response_model=schemas.ResearchCampaignOut)
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    item = crud.get_research_campaign(db, campaign_id)
    if not item:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return item


@router.post("", response_model=schemas.ResearchCampaignOut)
def create_campaign(payload: schemas.ResearchCampaignCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_research_campaign(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/{campaign_id}", response_model=schemas.ResearchCampaignOut)
def update_campaign(campaign_id: int, payload: schemas.ResearchCampaignUpdate, db: Session = Depends(get_db)):
    try:
        item = crud.update_research_campaign(db, campaign_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return item


@router.delete("/{campaign_id}")
def delete_campaign(campaign_id: int, db: Session = Depends(get_db)):
    try:
        result = crud.delete_research_campaign(db, campaign_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return result


@router.get("/{campaign_id}/clients", response_model=list[schemas.ClientOut])
def campaign_clients(campaign_id: int, db: Session = Depends(get_db)):
    return crud.list_campaign_clients(db, campaign_id)


@router.get("/{campaign_id}/templates", response_model=list[schemas.InterviewTemplateOut])
def campaign_templates(campaign_id: int, db: Session = Depends(get_db)):
    return crud.list_campaign_templates(db, campaign_id)


@router.get("/{campaign_id}/interviews", response_model=list[schemas.InterviewSessionOut])
def campaign_interviews(
    campaign_id: int,
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.list_campaign_interviews(db, campaign_id, limit=limit, offset=offset)
