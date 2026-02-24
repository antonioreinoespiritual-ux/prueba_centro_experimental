from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import SessionLocal

router = APIRouter(tags=["interviews"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# Canonical API namespace (/api)
# -----------------------------
@router.post("/api/interviews/templates", response_model=schemas.InterviewTemplateOut)
def create_template(payload: schemas.InterviewTemplateCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_interview_template(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/interviews/templates", response_model=list[schemas.InterviewTemplateOut])
def list_templates(
    project_id: int | None = Query(default=None),
    campaign_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return crud.list_interview_templates(db, project_id=project_id, campaign_id=campaign_id)


@router.get("/api/interviews/templates/{template_id}", response_model=schemas.InterviewTemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    item = crud.get_interview_template(db, template_id)
    if not item:
        raise HTTPException(status_code=404, detail="Interview template not found")
    return item


@router.patch("/api/interviews/templates/{template_id}", response_model=schemas.InterviewTemplateOut)
def update_template(template_id: int, payload: schemas.InterviewTemplateUpdate, db: Session = Depends(get_db)):
    try:
        item = crud.update_interview_template(db, template_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=404, detail="Interview template not found")
    return item


@router.delete("/api/interviews/templates/{template_id}")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    result = crud.delete_interview_template(db, template_id)
    if not result:
        raise HTTPException(status_code=404, detail="Interview template not found")
    return result


@router.get("/api/interviews/projects/{project_id}/templates", response_model=list[schemas.InterviewTemplateOut])
def list_project_templates(project_id: int, db: Session = Depends(get_db)):
    return crud.list_interview_templates(db, project_id=project_id)


@router.post("/api/interviews", response_model=schemas.InterviewSessionOut)
def create_interview(payload: schemas.InterviewSessionCreateV2, db: Session = Depends(get_db)):
    try:
        return crud.create_interview_v2(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/interviews", response_model=list[schemas.InterviewSessionOut])
def list_interviews(
    project_id: int | None = Query(default=None),
    hypothesis_id: int | None = Query(default=None),
    client_id: int | None = Query(default=None),
    campaign_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.list_interviews_v2(db, project_id=project_id, hypothesis_id=hypothesis_id, client_id=client_id, campaign_id=campaign_id, limit=limit, offset=offset)


@router.get("/api/interviews/{interview_id}", response_model=schemas.InterviewSessionOut)
def get_interview(interview_id: int, db: Session = Depends(get_db)):
    item = crud.get_interview_session(db, interview_id)
    if not item:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return item


@router.patch("/api/interviews/{interview_id}", response_model=schemas.InterviewSessionOut)
def patch_interview(interview_id: int, payload: schemas.InterviewSessionPatchV2, db: Session = Depends(get_db)):
    try:
        item = crud.patch_interview_v2(db, interview_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not item:
        raise HTTPException(status_code=404, detail="Interview session not found")
    return item


@router.post("/api/interviews/{interview_id}/attachments", response_model=schemas.InterviewAttachmentOut)
def upload_interview_attachment(interview_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    interview = crud.get_interview_session(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview session not found")
    base_dir = Path("data/uploads/interviews") / str(interview_id)
    base_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid4().hex}_{Path(file.filename or 'attachment').name}"
    destination = base_dir / safe_name
    content = file.file.read()
    destination.write_bytes(content)
    return crud.create_interview_attachment(
        db,
        interview_id=interview_id,
        filename=file.filename or safe_name,
        content_type=file.content_type,
        size=len(content),
        storage_path=str(destination),
    )


@router.get("/api/interviews/{interview_id}/attachments", response_model=list[schemas.InterviewAttachmentOut])
def list_attachments(interview_id: int, db: Session = Depends(get_db)):
    return crud.list_interview_attachments(db, interview_id)


@router.delete("/api/attachments/{attachment_id}")
def delete_attachment(attachment_id: int, db: Session = Depends(get_db)):
    obj = crud.delete_attachment(db, attachment_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Attachment not found")
    try:
        Path(obj.storage_path).unlink(missing_ok=True)
    except OSError:
        pass
    return {"deleted": True, "attachment_id": attachment_id}


# -----------------------------
# Backward-compatible legacy endpoints
# -----------------------------
@router.post("/interviews/sessions", response_model=schemas.InterviewSessionOut)
def create_session(payload: schemas.InterviewSessionCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_interview_session(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/interviews/sessions", response_model=list[schemas.InterviewSessionOut])
def list_sessions(
    project_id: int | None = Query(default=None),
    campaign_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    sessions = crud.list_interview_sessions(db, project_id=project_id)
    if campaign_id is not None:
        sessions = [s for s in sessions if s.campaign_id == campaign_id]
    return sessions


@router.get("/interviews/projects/{project_id}/sessions", response_model=list[schemas.InterviewSessionOut])
def list_project_sessions(project_id: int, db: Session = Depends(get_db)):
    return crud.list_interview_sessions(db, project_id=project_id)
