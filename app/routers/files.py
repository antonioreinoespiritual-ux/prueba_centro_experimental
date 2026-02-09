# app/routers/files.py
from __future__ import annotations

import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import SessionLocal
from ..storage import (
    MAX_UPLOAD_BYTES,
    build_entity_folder,
    build_file_path,
    build_stored_name,
    ensure_upload_dir,
    normalize_folder,
    remove_file,
    sanitize_filename,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_entity(db: Session, entity_type: schemas.EntityType, entity_id: int) -> None:
    if entity_type == "experiment":
        if not crud.get_experiment(db, entity_id):
            raise HTTPException(status_code=404, detail="Experiment not found")
    elif entity_type == "record":
        if not crud.get_record(db, entity_id):
            raise HTTPException(status_code=404, detail="Record not found")


@router.get("/{entity_type}/{entity_id}", response_model=list[schemas.EntityFileOut])
def list_files(
    entity_type: schemas.EntityType,
    entity_id: int,
    search: str | None = None,
    folder: str | None = None,
    db: Session = Depends(get_db),
):
    _ensure_entity(db, entity_type, entity_id)
    files = crud.list_entity_files(db, entity_type, entity_id)
    if folder is not None:
        normalized = normalize_folder(folder)
        files = [item for item in files if (item.folder or "") == (normalized or "")]
    if search:
        lowered = search.lower()
        files = [item for item in files if lowered in item.display_name.lower()]
    return files


@router.post("/{entity_type}/{entity_id}", response_model=list[schemas.EntityFileOut])
async def upload_files(
    entity_type: schemas.EntityType,
    entity_id: int,
    files: list[UploadFile] = File(...),
    folder: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    _ensure_entity(db, entity_type, entity_id)
    normalized_folder = normalize_folder(folder)
    results: list[schemas.EntityFileOut] = []
    for upload in files:
        display_name = sanitize_filename(upload.filename)
        stored_name = build_stored_name(display_name)
        target_dir = build_entity_folder(entity_type, entity_id, normalized_folder)
        ensure_upload_dir(target_dir)
        path = target_dir / stored_name
        size_bytes = 0
        try:
            with path.open("wb") as buffer:
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    size_bytes += len(chunk)
                    if size_bytes > MAX_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail="Archivo excede 3GB.")
                    buffer.write(chunk)
        except HTTPException:
            remove_file(path)
            raise
        except Exception as exc:
            remove_file(path)
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        finally:
            await upload.close()
        stored = crud.create_entity_file(
            db,
            entity_type=entity_type,
            entity_id=entity_id,
            display_name=display_name,
            stored_name=stored_name,
            folder=normalized_folder,
            content_type=upload.content_type,
            size_bytes=size_bytes,
        )
        results.append(stored)
    return results


@router.get("/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    file_obj = crud.get_entity_file(db, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    path = build_file_path(file_obj.entity_type, file_obj.entity_id, file_obj.stored_name, file_obj.folder)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco.")
    return FileResponse(
        path=str(path),
        filename=file_obj.display_name,
        media_type=file_obj.content_type or "application/octet-stream",
    )


@router.patch("/{file_id}", response_model=schemas.EntityFileOut)
def rename_file(file_id: int, payload: schemas.EntityFileRename, db: Session = Depends(get_db)):
    file_obj = crud.get_entity_file(db, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")

    updated_name = file_obj.display_name
    if payload.display_name is not None:
        updated_name = sanitize_filename(payload.display_name)
    updated_folder = file_obj.folder
    if payload.folder is not None:
        updated_folder = normalize_folder(payload.folder)

    if updated_folder != file_obj.folder:
        old_path = build_file_path(
            file_obj.entity_type,
            file_obj.entity_id,
            file_obj.stored_name,
            file_obj.folder,
        )
        new_path = build_file_path(
            file_obj.entity_type,
            file_obj.entity_id,
            file_obj.stored_name,
            updated_folder,
        )
        ensure_upload_dir(new_path.parent)
        if old_path.exists():
            shutil.move(str(old_path), str(new_path))

    updated = crud.update_entity_file(
        db,
        file_id=file_id,
        display_name=updated_name,
        folder=updated_folder,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    return updated


@router.delete("/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    file_obj = crud.get_entity_file(db, file_id)
    if not file_obj:
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")
    path = build_file_path(file_obj.entity_type, file_obj.entity_id, file_obj.stored_name, file_obj.folder)
    remove_file(path)
    crud.delete_entity_file(db, file_id)
    return {"deleted": True, "file_id": file_id}
