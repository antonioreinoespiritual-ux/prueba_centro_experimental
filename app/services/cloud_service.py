from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import re
import shutil
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from .drive_sync_service import CLOUD_PROJECTS_DIR, _normalize_project_key, get_or_create_project
from ..storage import sanitize_filename

CLOUD_ROOT = Path(os.getenv("CLOUD_ROOT", "/Users/m2/CloudDriveData")).expanduser()
SYSTEM_LIBRARY_NAME = "_System"


def _ensure_cloud_root() -> Path:
    CLOUD_ROOT.mkdir(parents=True, exist_ok=True)
    return CLOUD_ROOT


def _sanitize_segment(segment: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _.-]", "_", segment).strip()
    return cleaned[:100] if cleaned else "untitled"


def _sanitize_name(name: str) -> str:
    cleaned = _sanitize_segment(name)
    return cleaned or "untitled"


def _build_rel_path(parent: models.CloudItem | None, name: str) -> str:
    if parent and parent.rel_path:
        return f"{parent.rel_path}/{name}"
    return name


def _resolve_path(library: models.CloudLibrary, rel_path: str | None = None) -> Path:
    base = Path(library.root_path)
    if rel_path:
        candidate = (base / rel_path).resolve()
    else:
        candidate = base.resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError as exc:
        raise ValueError("Invalid path traversal detected") from exc
    return candidate


def _get_descendants(db: Session, library_id: int, base_rel: str) -> Iterable[models.CloudItem]:
    stmt = select(models.CloudItem).where(
        models.CloudItem.library_id == library_id,
        models.CloudItem.rel_path.like(f"{base_rel}/%"),
    )
    return db.scalars(stmt).all()


def ensure_system_library(db: Session) -> models.CloudLibrary:
    library = db.scalars(
        select(models.CloudLibrary).where(
            (models.CloudLibrary.is_system.is_(True))
            | (models.CloudLibrary.name == SYSTEM_LIBRARY_NAME)
        )
    ).first()
    if library:
        if not library.is_system:
            library.is_system = True
        if not library.root_path or library.root_path != str(_ensure_cloud_root().resolve()):
            library.root_path = str(_ensure_cloud_root().resolve())
        db.add(library)
        db.commit()
        db.refresh(library)
        return library

    library = models.CloudLibrary(
        name=SYSTEM_LIBRARY_NAME,
        owner_id="system",
        root_path=str(_ensure_cloud_root().resolve()),
        is_system=True,
    )
    db.add(library)
    db.commit()
    db.refresh(library)
    return library


def list_libraries(db: Session) -> list[models.CloudLibrary]:
    ensure_system_library(db)
    stmt = select(models.CloudLibrary).order_by(
        models.CloudLibrary.is_system.desc(),
        models.CloudLibrary.created_at.desc(),
    )
    return db.scalars(stmt).all()


def create_library(db: Session, name: str, owner_id: str | None) -> models.CloudLibrary:
    _ensure_cloud_root()
    if name == SYSTEM_LIBRARY_NAME:
        return ensure_system_library(db)
    safe_name = _sanitize_segment(name)
    library = models.CloudLibrary(name=name, owner_id=owner_id, root_path="")
    db.add(library)
    db.commit()
    db.refresh(library)
    library_folder = f"{library.id}_{safe_name}"
    root_path = (_ensure_cloud_root() / library_folder).resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    library.root_path = str(root_path)
    db.add(library)
    db.commit()
    db.refresh(library)
    return library


def ensure_library_root(db: Session, library: models.CloudLibrary) -> models.CloudLibrary:
    if library.is_system:
        root_path = str(_ensure_cloud_root().resolve())
        if library.root_path != root_path:
            library.root_path = root_path
            db.add(library)
            db.commit()
            db.refresh(library)
        return library
    if library.root_path:
        return library
    safe_name = _sanitize_segment(library.name)
    root_path = (_ensure_cloud_root() / f"{library.id}_{safe_name}").resolve()
    root_path.mkdir(parents=True, exist_ok=True)
    library.root_path = str(root_path)
    db.add(library)
    db.commit()
    db.refresh(library)
    return library


def list_items(db: Session, parent_id: int | None, library_id: int | None) -> list[models.CloudItem]:
    if library_id is None:
        return []
    library = db.get(models.CloudLibrary, library_id)
    if not library:
        return []
    library = ensure_library_root(db, library)

    parent = db.get(models.CloudItem, parent_id) if parent_id else None
    target_rel = parent.rel_path or parent.path if parent else None
    target_dir = _resolve_path(library, target_rel)

    if not target_dir.exists():
        target_dir.mkdir(parents=True, exist_ok=True)

    existing = {}
    for item in db.scalars(
        select(models.CloudItem).where(
            models.CloudItem.library_id == library_id,
            models.CloudItem.parent_id == (parent_id if parent else None),
        )
    ).all():
        key = item.rel_path or item.path
        if key:
            existing[key] = item

    items: list[models.CloudItem] = []
    for entry in sorted(target_dir.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
        rel_path = str(entry.relative_to(Path(library.root_path)))
        item = existing.get(rel_path)
        if not item:
            item = models.CloudItem(
                name=entry.name,
                library_id=library_id,
                parent_id=parent_id,
                item_type="folder" if entry.is_dir() else "file",
                size=entry.stat().st_size if entry.is_file() else None,
                rel_path=rel_path,
                path=rel_path,
            )
            db.add(item)
            db.commit()
            db.refresh(item)
        else:
            updated = False
            item.name = entry.name
            item.item_type = "folder" if entry.is_dir() else "file"
            if entry.is_file():
                size = entry.stat().st_size
                if item.size != size:
                    item.size = size
                    updated = True
            if item.rel_path != rel_path:
                item.rel_path = rel_path
                item.path = rel_path
                updated = True
            if updated:
                db.add(item)
                db.commit()
                db.refresh(item)
        items.append(item)

    return items


def create_folder(
    db: Session,
    name: str,
    library_id: int,
    parent_id: int | None,
    owner_id: str | None,
) -> models.CloudItem:
    library = db.get(models.CloudLibrary, library_id)
    if not library:
        raise ValueError("Library not found")
    library = ensure_library_root(db, library)

    parent = db.get(models.CloudItem, parent_id) if parent_id else None
    safe_name = _sanitize_name(name)
    rel_path = _build_rel_path(parent, safe_name)
    folder_path = _resolve_path(library, rel_path)
    if folder_path.exists():
        raise ValueError("Folder already exists")
    folder_path.mkdir(parents=True, exist_ok=True)
    folder = models.CloudItem(
        name=safe_name,
        library_id=library_id,
        parent_id=parent_id,
        item_type="folder",
        rel_path=rel_path,
        path=rel_path,
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
    library = db.get(models.CloudLibrary, library_id)
    if not library:
        raise ValueError("Library not found")
    ensure_library_root(db, library)
    parent = db.get(models.CloudItem, parent_id) if parent_id else None
    safe_name = sanitize_filename(name)
    rel_path = _build_rel_path(parent, safe_name)
    item = models.CloudItem(
        name=safe_name,
        library_id=library_id,
        parent_id=parent_id,
        item_type="file",
        size=size,
        rel_path=rel_path,
        path=rel_path,
        owner_id=owner_id,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def rename_item(db: Session, item: models.CloudItem, new_name: str, library: models.CloudLibrary) -> models.CloudItem:
    safe_name = _sanitize_name(new_name)
    old_rel = item.rel_path or item.name
    parent = item.parent
    new_rel = _build_rel_path(parent, safe_name)

    old_path = _resolve_path(library, old_rel)
    new_path = _resolve_path(library, new_rel)
    old_path.rename(new_path)

    item.name = safe_name
    item.rel_path = new_rel
    item.path = new_rel
    db.add(item)

    if item.item_type == "folder":
        for child in _get_descendants(db, item.library_id, old_rel):
            if child.rel_path:
                child.rel_path = child.rel_path.replace(old_rel, new_rel, 1)
                child.path = child.rel_path
                db.add(child)
    db.commit()
    db.refresh(item)
    return item


def move_item(
    db: Session,
    item: models.CloudItem,
    new_parent: models.CloudItem | None,
    library: models.CloudLibrary,
) -> models.CloudItem:
    old_rel = item.rel_path or item.name
    new_rel = _build_rel_path(new_parent, item.name)

    old_path = _resolve_path(library, old_rel)
    new_path = _resolve_path(library, new_rel)
    new_path.parent.mkdir(parents=True, exist_ok=True)
    old_path.rename(new_path)

    item.parent_id = new_parent.id if new_parent else None
    item.rel_path = new_rel
    item.path = new_rel
    db.add(item)

    if item.item_type == "folder":
        for child in _get_descendants(db, item.library_id, old_rel):
            if child.rel_path:
                child.rel_path = child.rel_path.replace(old_rel, new_rel, 1)
                child.path = child.rel_path
                db.add(child)
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: models.CloudItem, library: models.CloudLibrary) -> None:
    rel_path = item.rel_path or item.name
    target = _resolve_path(library, rel_path)
    if item.item_type == "folder":
        if target.exists():
            shutil.rmtree(target)
    else:
        if target.exists():
            target.unlink()

    if item.item_type == "folder" and rel_path:
        for child in _get_descendants(db, item.library_id, rel_path):
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


def build_display_map(
    db: Session,
    library_id: int | None,
    parent_id: int | None,
) -> list[dict[str, str | int | None]]:
    if library_id is None:
        return []
    items = list_items(db, parent_id=parent_id, library_id=library_id)
    entries: list[dict[str, str | int | None]] = []
    for item in items:
        display_name: str | None = None
        badge: str | None = None
        if item.item_type == "folder":
            if item.name == "_System":
                display_name = "Sistema"
            elif item.name == "_Archived":
                display_name = "Archivados"
            rel_path = item.rel_path or item.path
            if rel_path:
                match = re.match(rf"^{re.escape(CLOUD_PROJECTS_DIR)}/([^/]+)$", rel_path)
                if match:
                    project = db.scalars(
                        select(models.CloudProject).where(
                            models.CloudProject.folder_path == f\"{CLOUD_PROJECTS_DIR}/{match.group(1)}\"
                        )
                    ).first()
                    if project:
                        display_name = project.project_name
            match = re.match(r"^H(\d+)_", item.name)
            if match:
                exp_id = int(match.group(1))
                experiment = db.get(models.Experiment, exp_id)
                if experiment:
                    display_name = (
                        (experiment.independent_variable or "").strip()
                        or (experiment.metric_x or "").strip()
                        or f"Hipótesis {exp_id}"
                    )
                    badge = f"H{exp_id}"
            match = re.match(r"^R(\d+)_", item.name)
            if match:
                record_id = int(match.group(1))
                record = db.get(models.ExperimentRecord, record_id)
                if record:
                    display_name = (record.record_name or "").strip() or f"Record {record_id}"
                    badge = f"R{record_id}"
        if display_name:
            entries.append({"item_id": item.id, "display_name": display_name, "badge": badge})
    return entries


def list_projects(db: Session) -> list[models.CloudProject]:
    projects = db.scalars(select(models.CloudProject).order_by(models.CloudProject.project_name.asc())).all()
    if projects:
        return projects
    experiments = db.scalars(select(models.Experiment)).all()
    for experiment in experiments:
        if experiment.project_name:
            get_or_create_project(db, experiment.project_name)
    return db.scalars(select(models.CloudProject).order_by(models.CloudProject.project_name.asc())).all()


def list_project_hypotheses(db: Session, project_id: int) -> list[models.Experiment]:
    project = db.get(models.CloudProject, project_id)
    if not project:
        return []
    stmt = select(models.Experiment).where(
        models.Experiment.project_name.is_not(None)
    )
    experiments = db.scalars(stmt).all()
    return [
        experiment
        for experiment in experiments
        if _normalize_project_key(experiment.project_name) == project.project_key
    ]


def hypothesis_display_name(experiment: models.Experiment) -> str:
    independent_variable = (experiment.independent_variable or "").strip()
    if independent_variable:
        return independent_variable
    metric_x = (experiment.metric_x or "").strip()
    if metric_x:
        return metric_x
    return f"Hipótesis {experiment.id}"


def list_projects_tree(db: Session) -> list[dict[str, object]]:
    projects: list[dict[str, object]] = []
    for project in list_projects(db):
        project_root = (CLOUD_ROOT / project.folder_path).resolve()
        hypotheses: list[dict[str, object]] = []
        hypotheses_dir = project_root / "Hypotheses"
        if hypotheses_dir.exists():
            for hypothesis_dir in sorted(hypotheses_dir.iterdir(), key=lambda p: p.name.lower()):
                if not hypothesis_dir.is_dir():
                    continue
                hypothesis_rel = f"{project.folder_path}/Hypotheses/{hypothesis_dir.name}"
                records_dir = hypothesis_dir / "Records"
                records: list[dict[str, str]] = []
                if records_dir.exists():
                    for record_dir in sorted(records_dir.iterdir(), key=lambda p: p.name.lower()):
                        if record_dir.is_dir():
                            records.append(
                                {
                                    "name": record_dir.name,
                                    "rel_path": f"{hypothesis_rel}/Records/{record_dir.name}",
                                }
                            )
                hypotheses.append(
                    {
                        "name": hypothesis_dir.name,
                        "rel_path": hypothesis_rel,
                        "records": records,
                    }
                )
        projects.append(
            {
                "name": project.project_name,
                "rel_path": project.folder_path,
                "hypotheses": hypotheses,
            }
        )
    return projects


def resolve_item_path(library: models.CloudLibrary, item: models.CloudItem) -> Path:
    rel_path = item.rel_path or item.path or item.name
    return _resolve_path(library, rel_path)


def resolve_parent_path(library: models.CloudLibrary, parent: models.CloudItem | None) -> Path:
    rel_path = parent.rel_path or parent.path if parent else None
    return _resolve_path(library, rel_path)
