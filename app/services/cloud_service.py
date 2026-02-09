from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session
from sqlalchemy import select

from .. import models
from ..storage import ensure_upload_dir

CLOUD_STORAGE_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "cloud"


def _build_path(parent: models.CloudItem | None, name: str) -> str:
    if parent and parent.path:
        return f"{parent.path}/{name}"
    if parent and parent.name:
        return f"{parent.name}/{name}"
    return name


def _get_descendants(db: Session, base_path: str) -> Iterable[models.CloudItem]:
    stmt = select(models.CloudItem).where(models.CloudItem.path.like(f"{base_path}/%"))
    return db.scalars(stmt).all()


def list_libraries(db: Session) -> list[models.CloudLibrary]:
    return db.scalars(select(models.CloudLibrary).order_by(models.CloudLibrary.created_at.desc())).all()


def create_library(db: Session, name: str, owner_id: str | None) -> models.CloudLibrary:
    library = models.CloudLibrary(name=name, owner_id=owner_id)
    db.add(library)
    db.commit()
    db.refresh(library)
    return library


def list_items(db: Session, parent_id: int | None, library_id: int | None) -> list[models.CloudItem]:
    stmt = select(models.CloudItem)
    if parent_id is None:
        stmt = stmt.where(models.CloudItem.parent_id.is_(None))
    else:
        stmt = stmt.where(models.CloudItem.parent_id == parent_id)
    if library_id is not None:
        stmt = stmt.where(models.CloudItem.library_id == library_id)
    stmt = stmt.order_by(models.CloudItem.item_type.desc(), models.CloudItem.name.asc())
    return db.scalars(stmt).all()


def create_folder(
    db: Session,
    name: str,
    library_id: int,
    parent_id: int | None,
    owner_id: str | None,
) -> models.CloudItem:
    parent = db.get(models.CloudItem, parent_id) if parent_id else None
    path = _build_path(parent, name)
    folder = models.CloudItem(
        name=name,
        library_id=library_id,
        parent_id=parent_id,
        item_type="folder",
        path=path,
        owner_id=owner_id,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


def create_file_item(
    db: Session,
    name: str,
    library_id: int,
    parent_id: int | None,
    owner_id: str | None,
    size: int | None,
) -> models.CloudItem:
    parent = db.get(models.CloudItem, parent_id) if parent_id else None
    path = _build_path(parent, name)
    item = models.CloudItem(
        name=name,
        library_id=library_id,
        parent_id=parent_id,
        item_type="file",
        size=size,
        path=path,
        owner_id=owner_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def rename_item(db: Session, item: models.CloudItem, new_name: str) -> models.CloudItem:
    old_path = item.path or item.name
    item.name = new_name
    item.path = _build_path(item.parent, new_name)
    db.add(item)
    if item.item_type == "folder" and old_path:
        for child in _get_descendants(db, old_path):
            if child.path:
                child.path = child.path.replace(old_path, item.path or item.name, 1)
            db.add(child)
    db.commit()
    db.refresh(item)
    return item


def move_item(db: Session, item: models.CloudItem, new_parent: models.CloudItem | None) -> models.CloudItem:
    old_path = item.path or item.name
    item.parent_id = new_parent.id if new_parent else None
    item.path = _build_path(new_parent, item.name)
    db.add(item)
    if item.item_type == "folder" and old_path:
        for child in _get_descendants(db, old_path):
            if child.path:
                child.path = child.path.replace(old_path, item.path or item.name, 1)
            db.add(child)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: models.CloudItem) -> None:
    base_path = item.path or item.name
    if item.item_type == "folder" and base_path:
        for child in _get_descendants(db, base_path):
            db.delete(child)
    db.delete(item)
    db.commit()


def log_action(db: Session, item_id: int | None, action: str, user_id: str | None) -> None:
    audit = models.CloudAudit(item_id=item_id, action=action, user_id=user_id, timestamp=datetime.utcnow())
    db.add(audit)
    db.commit()


def create_share(db: Session, item_id: int, shared_with: str, permission: str) -> models.CloudShare:
    share = models.CloudShare(item_id=item_id, shared_with=shared_with, permission=permission)
    db.add(share)
    db.commit()
    db.refresh(share)
    return share


def list_shares(db: Session, item_id: int) -> list[models.CloudShare]:
    return db.scalars(select(models.CloudShare).where(models.CloudShare.item_id == item_id)).all()


def search_items(db: Session, query: str) -> list[models.CloudItem]:
    stmt = select(models.CloudItem).where(models.CloudItem.name.ilike(f"%{query}%"))
    return db.scalars(stmt).all()


def ensure_cloud_dir(library_id: int) -> Path:
    path = CLOUD_STORAGE_ROOT / str(library_id)
    ensure_upload_dir(path)
    return path
