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


@router.get("/cloud")
def cloud_app():
    spa_index = STATIC_DIR / "cloud" / "index.html"
    legacy = STATIC_DIR / "cloud.html"
    if spa_index.exists():
        return FileResponse(str(spa_index))
    return FileResponse(str(legacy))


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
async def complete_upload(
    file: UploadFile = File(...),
    filename: str = Form(...),
    library_id: int = Form(...),
    parent_id: int | None = Form(default=None),
    owner_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    safe_name = sanitize_filename(filename)
    library = db.get(models.CloudLibrary, library_id)
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")
    library = cloud_service.ensure_library_root(db, library)
    if parent_id:
        parent = db.get(models.CloudItem, parent_id)
        if not parent or parent.item_type != "folder":
            raise HTTPException(status_code=400, detail="Parent must be a folder")
    item = cloud_service.create_file_item(
        db,
        name=safe_name,
        library_id=library_id,
        parent_id=parent_id,
        owner_id=owner_id,
        size=None,
    )
    parent = db.get(models.CloudItem, parent_id) if parent_id else None
    try:
        target_dir = cloud_service.resolve_parent_path(library, parent)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    target_dir.mkdir(parents=True, exist_ok=True)
    stored_path = target_dir / safe_name
    contents = await file.read()
    stored_path.write_bytes(contents)
    item.size = len(contents)
    item.rel_path = str(stored_path.relative_to(Path(library.root_path)))
    item.path = item.rel_path
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/api/cloud/files/{file_id}/download")
def download_file(file_id: int, db: Session = Depends(get_db)):
    item = db.get(models.CloudItem, file_id)
    if not item or item.item_type != "file":
        raise HTTPException(status_code=404, detail="File not found")
    library = db.get(models.CloudLibrary, item.library_id)
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")
    library = cloud_service.ensure_library_root(db, library)
    try:
        file_path = cloud_service.resolve_item_path(library, item)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File missing on disk")
    return FileResponse(str(file_path), filename=item.name)


@router.post("/api/cloud/items/{item_id}/share", response_model=schemas.CloudShareOut)
def share_item(item_id: int, payload: schemas.CloudShareCreate, db: Session = Depends(get_db)):
    item = db.get(models.CloudItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return cloud_service.create_share(db, item_id=item_id, shared_with=payload.shared_with, permission=payload.permission)


@router.get("/api/cloud/items/{item_id}/shares", response_model=list[schemas.CloudShareOut])
def list_item_shares(item_id: int, db: Session = Depends(get_db)):
    return cloud_service.list_shares(db, item_id=item_id)


@router.get("/api/cloud/search", response_model=schemas.CloudSearchResponse)
def search_items(q: str, db: Session = Depends(get_db)):
    results = cloud_service.search_items(db, q)
    return schemas.CloudSearchResponse(results=results)


@router.get("/api/cloud/display-map", response_model=schemas.CloudDisplayMap)
def display_map(
    library_id: int,
    parent_id: int | None = None,
    db: Session = Depends(get_db),
):
    items = cloud_service.build_display_map(db, library_id=library_id, parent_id=parent_id)
    return schemas.CloudDisplayMap(items=items)
