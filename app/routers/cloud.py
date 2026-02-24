from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path
from sqlalchemy.orm import Session

from ..database import SessionLocal
from .. import schemas, models
from ..services import cloud_service
from ..storage import sanitize_filename


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _cloud_build_available() -> bool:
    spa_index = STATIC_DIR / "cloud" / "index.html"
    assets_dir = STATIC_DIR / "cloud" / "assets"
    if not spa_index.exists() or not assets_dir.exists():
        return False
    return any(assets_dir.glob("*.js"))


def _serve_cloud_ui() -> FileResponse:
    if _cloud_build_available():
        return FileResponse(str(STATIC_DIR / "cloud" / "index.html"), media_type="text/html")
    fallback = STATIC_DIR / "cloud_fallback.html"
    if fallback.exists():
        return FileResponse(str(fallback), media_type="text/html")
    return FileResponse(str(STATIC_DIR / "cloud.html"), media_type="text/html")


@router.get("/cloud")
def cloud_app():
    return _serve_cloud_ui()


@router.get("/cloud/{path:path}")
def cloud_spa_fallback(path: str):
    return _serve_cloud_ui()


@router.get("/api/cloud/libraries", response_model=list[schemas.CloudLibraryOut])
def list_libraries(db: Session = Depends(get_db)):
    return cloud_service.list_libraries(db)


@router.post("/api/cloud/libraries", response_model=schemas.CloudLibraryOut)
def create_library(payload: schemas.CloudLibraryCreate, db: Session = Depends(get_db)):
    return cloud_service.create_library(db, payload.name.strip(), payload.owner_id)


@router.get("/api/cloud/items", response_model=list[schemas.CloudItemOut])
def list_items(
    parent_id: int | None = None,
    library_id: int | None = None,
    db: Session = Depends(get_db),
):
    return cloud_service.list_items(db, parent_id=parent_id, library_id=library_id)


@router.post("/api/cloud/folders", response_model=schemas.CloudItemOut)
def create_folder(payload: schemas.CloudItemCreate, db: Session = Depends(get_db)):
    if payload.parent_id:
        parent = db.get(models.CloudItem, payload.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent folder not found")
        if parent.item_type != "folder":
            raise HTTPException(status_code=400, detail="Parent must be a folder")
        if parent.library_id != payload.library_id:
            raise HTTPException(status_code=400, detail="Parent belongs to a different library")
    try:
        return cloud_service.create_folder(
            db,
            name=payload.name.strip(),
            library_id=payload.library_id,
            parent_id=payload.parent_id,
            owner_id=payload.owner_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/api/cloud/items/{item_id}", response_model=schemas.CloudItemOut)
def update_item(item_id: int, payload: schemas.CloudItemUpdate, db: Session = Depends(get_db)):
    item = db.get(models.CloudItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    library = db.get(models.CloudLibrary, item.library_id)
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")
    library = cloud_service.ensure_library_root(db, library)
    try:
        if payload.name:
            item = cloud_service.rename_item(db, item, payload.name.strip(), library)
        if payload.parent_id is not None:
            parent = db.get(models.CloudItem, payload.parent_id) if payload.parent_id else None
            if parent and parent.item_type != "folder":
                raise HTTPException(status_code=400, detail="Parent must be a folder")
            if parent and parent.library_id != item.library_id:
                raise HTTPException(status_code=400, detail="Parent belongs to a different library")
            item = cloud_service.move_item(db, item, parent, library)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return item


@router.delete("/api/cloud/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.CloudItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    library = db.get(models.CloudLibrary, item.library_id)
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")
    library = cloud_service.ensure_library_root(db, library)
    cloud_service.delete_item(db, item, library)
    return {"deleted": True, "item_id": item_id}


@router.post("/api/cloud/files/init-upload")
def init_upload(payload: schemas.CloudUploadInit):
    return {
        "upload_id": f"local-{payload.library_id}-{payload.filename}",
        "upload_url": "/api/cloud/files/complete-upload",
        "status": "ready",
    }


@router.post("/api/cloud/files/complete-upload", response_model=schemas.CloudItemOut)
def complete_upload(
    filename: str = Form(...),
    library_id: int = Form(...),
    parent_id: int | None = Form(default=None),
    owner_id: int | None = Form(default=None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    try:
        content = file.file.read()
        safe_name = sanitize_filename(filename)
        return cloud_service.save_uploaded_file(
            db,
            filename=safe_name,
            library_id=library_id,
            parent_id=parent_id,
            owner_id=owner_id,
            content=content,
            content_type=file.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/cloud/files/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    item = db.get(models.CloudItem, file_id)
    if not item or item.item_type != "file":
        raise HTTPException(status_code=404, detail="File not found")
    if not item.storage_path:
        raise HTTPException(status_code=404, detail="File has no storage path")
    file_path = Path(item.storage_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Stored file not found")
    return FileResponse(str(file_path), filename=item.name)


@router.post("/api/cloud/items/{item_id}/share", response_model=schemas.CloudShareOut)
def create_share(item_id: int, payload: schemas.CloudShareCreate, db: Session = Depends(get_db)):
    item = db.get(models.CloudItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return cloud_service.create_share(db, item, payload.permission, payload.expires_at)


@router.get("/api/cloud/items/{item_id}/shares", response_model=list[schemas.CloudShareOut])
def list_shares(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.CloudItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return cloud_service.list_shares(db, item)


@router.get("/api/cloud/search", response_model=schemas.CloudSearchResponse)
def search_cloud(
    q: str,
    library_id: int | None = None,
    limit: int = 25,
    db: Session = Depends(get_db),
):
    return cloud_service.search(db, q=q.strip(), library_id=library_id, limit=limit)


@router.get("/api/cloud/hypotheses/{hypothesis_id}/records", response_model=list[schemas.CloudItemOut])
def list_hypothesis_records(hypothesis_id: int, db: Session = Depends(get_db)):
    return cloud_service.list_hypothesis_records(db, hypothesis_id)


@router.get("/api/cloud/display-map", response_model=schemas.CloudDisplayMap)
def cloud_display_map(db: Session = Depends(get_db)):
    return cloud_service.get_display_map(db)


@router.get("/api/cloud/tree/projects", response_model=schemas.CloudProjectsTree)
def cloud_projects_tree(db: Session = Depends(get_db)):
    return cloud_service.get_projects_tree(db)


@router.get("/api/cloud/projects", response_model=list[schemas.CloudProjectOut])
def list_cloud_projects(db: Session = Depends(get_db)):
    return cloud_service.list_projects(db)


@router.get("/api/cloud/projects/{project_id}/hypotheses", response_model=list[schemas.CloudProjectHypothesisOut])
def list_cloud_project_hypotheses(project_id: int, db: Session = Depends(get_db)):
    return cloud_service.list_project_hypotheses(db, project_id)
