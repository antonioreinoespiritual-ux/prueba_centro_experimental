from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter(prefix="/interviews", tags=["interviews"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/templates", response_model=schemas.InterviewTemplateOut)
def create_template(payload: schemas.InterviewTemplateCreate, db: Session = Depends(get_db)):
    return crud.create_interview_template(db, payload)


@router.get("/templates", response_model=list[schemas.InterviewTemplateOut])
def list_templates(project_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    return crud.list_interview_templates(db, project_id=project_id)


@router.get("/templates/{template_id}", response_model=schemas.InterviewTemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    item = crud.get_interview_template(db, template_id)
    if not item:
        raise HTTPException(status_code=404, detail="Interview template not found")
    return item


@router.patch("/templates/{template_id}", response_model=schemas.InterviewTemplateOut)
def update_template(template_id: int, payload: schemas.InterviewTemplateUpdate, db: Session = Depends(get_db)):
    item = crud.update_interview_template(db, template_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Interview template not found")
    return item


@router.delete("/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    result = crud.delete_interview_template(db, template_id)
    if not result:
        raise HTTPException(status_code=404, detail="Interview template not found")
    return result


@router.get("/projects/{project_id}/templates", response_model=list[schemas.InterviewTemplateOut])
def list_project_templates(project_id: int, db: Session = Depends(get_db)):
    return crud.list_interview_templates(db, project_id=project_id)


@router.post("/sessions", response_model=schemas.InterviewSessionOut)
def create_session(payload: schemas.InterviewSessionCreate, db: Session = Depends(get_db)):
    return crud.create_interview_session(db, payload)


@router.get("/sessions", response_model=list[schemas.InterviewSessionOut])
def list_sessions(project_id: int | None = Query(default=None), db: Session = Depends(get_db)):
    return crud.list_interview_sessions(db, project_id=project_id)


@router.get("/sessions/{session_id}", response_model=schemas.InterviewSessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    item = crud.get_interview_session(db, session_id)
    if not item:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return item


@router.patch("/sessions/{session_id}", response_model=schemas.InterviewSessionOut)
def update_session(session_id: int, payload: schemas.InterviewSessionUpdate, db: Session = Depends(get_db)):
    item = crud.update_interview_session(db, session_id, payload)
    if not item:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return item


@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db)):
    result = crud.delete_interview_session(db, session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return result


@router.get("/projects/{project_id}/sessions", response_model=list[schemas.InterviewSessionOut])
def list_project_sessions(project_id: int, db: Session = Depends(get_db)):
    return crud.list_interview_sessions(db, project_id=project_id)
