from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import os
import re
import shutil
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models


CLOUD_ROOT = Path(os.getenv("CLOUD_ROOT", "/Users/m2/CloudDriveData")).expanduser()
CLOUD_PROJECTS_DIR = "Projects"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DriveSyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0


def ensure_base_folders() -> None:
    for folder in (CLOUD_PROJECTS_DIR, "_System", "_Archived"):
        (CLOUD_ROOT / folder).mkdir(parents=True, exist_ok=True)


def _normalize_rel_path(rel_path: str | None) -> str | None:
    if not rel_path:
        return None
    cleaned = rel_path.replace("\\", "/")
    if os.path.isabs(cleaned):
        try:
            cleaned = str(Path(cleaned).resolve().relative_to(CLOUD_ROOT.resolve()))
        except ValueError as exc:
            raise ValueError("Invalid path traversal detected") from exc
    return cleaned.lstrip("/")


def safe_join(root: Path, rel_path: str | None) -> Path:
    normalized = _normalize_rel_path(rel_path) if rel_path else ""
    target = root / normalized
    resolved = target.resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("Invalid path traversal detected") from exc
    return resolved


def _slugify(value: str, max_len: int = 60) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-")
    if not cleaned:
        cleaned = "item"
    return cleaned[:max_len]


def _normalize_project_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9\\s-]", " ", normalized)
    normalized = re.sub(r"\\s+", " ", normalized).strip()
    return normalized or "proyecto"


def _normalize_folder_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or "item"


def _build_folder_name(prefix: str, item_id: int, name: str) -> str:
    return f"{prefix}{item_id}_{_slugify(name)}"


def _available_rel_path(base_folder: str, folder_name: str, current_rel: str | None = None) -> str:
    base_path = Path(base_folder)
    candidate = base_path / folder_name
    current_rel = _normalize_rel_path(current_rel) if current_rel else None
    if current_rel and candidate.as_posix() == current_rel.replace("\\", "/"):
        return candidate.as_posix()
    if not safe_join(CLOUD_ROOT, candidate.as_posix()).exists():
        return candidate.as_posix()
    suffix = 2
    while True:
        alt_name = f"{folder_name}-{suffix}"
        alt_rel = base_path / alt_name
        if not safe_join(CLOUD_ROOT, alt_rel.as_posix()).exists():
            return alt_rel.as_posix()
        suffix += 1


def _rename_if_needed(old_rel: str | None, new_rel: str) -> str:
    old_rel = _normalize_rel_path(old_rel)
    new_rel = _normalize_rel_path(new_rel) or ""
    if old_rel == new_rel:
        return new_rel
    old_path = safe_join(CLOUD_ROOT, old_rel) if old_rel else None
    new_path = safe_join(CLOUD_ROOT, new_rel)
    if old_path and old_path.exists():
        new_path.parent.mkdir(parents=True, exist_ok=True)
        if new_path.exists():
            new_rel = _relocate_with_suffix(old_path, new_path)
            return new_rel
        shutil.move(str(old_path), str(new_path))
    else:
        new_path.mkdir(parents=True, exist_ok=True)
    return new_rel


def _relocate_with_suffix(source: Path, dest: Path) -> str:
    suffix = 1
    while True:
        candidate = dest.parent / f"{dest.name}_dup{suffix}"
        if not candidate.exists():
            shutil.move(str(source), str(candidate))
            return str(candidate.relative_to(CLOUD_ROOT.resolve()))
        suffix += 1


def _pick_hypothesis_title(experiment: models.Experiment) -> str:
    independent_variable = (experiment.independent_variable or "").strip()
    if independent_variable:
        return independent_variable
    metric_x = (experiment.metric_x or "").strip()
    if metric_x:
        return metric_x
    return "sin-variable"


def _extract_folder_segment(rel_path: str | None, prefix: str) -> str | None:
    if not rel_path:
        return None
    normalized = _normalize_rel_path(rel_path)
    if not normalized:
        return None
    match_segment = None
    for segment in Path(normalized).parts:
        if re.match(rf"^{re.escape(prefix)}\d+_", segment):
            match_segment = segment
    return match_segment


def _move_tree_merge(source: Path, dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    moved = 0
    for entry in source.iterdir():
        target = dest / entry.name
        if target.exists():
            suffix = 1
            while True:
                candidate = dest / f"{entry.name}_dup{suffix}"
                if not candidate.exists():
                    target = candidate
                    break
                suffix += 1
        shutil.move(str(entry), str(target))
        moved += 1
    try:
        source.rmdir()
    except OSError:
        pass
    return moved


def _archive_path(name: str) -> Path:
    base = safe_join(CLOUD_ROOT, "_Archived")
    base.mkdir(parents=True, exist_ok=True)
    candidate = base / name
    if not candidate.exists():
        return candidate
    suffix = 1
    while True:
        candidate = base / f"{name}-{suffix}"
        if not candidate.exists():
            return candidate
        suffix += 1


def _consolidate_legacy_projects() -> dict[str, int]:
    projects_root = safe_join(CLOUD_ROOT, CLOUD_PROJECTS_DIR)
    consolidated = 0
    moved_items = 0
    if not projects_root.exists():
        return {"consolidated": 0, "moved_items": 0}
    for entry in projects_root.iterdir():
        if not entry.is_dir():
            continue
        match = re.match(r"^P\d+_(.+)$", entry.name)
        if not match:
            continue
        slug = match.group(1)
        target = projects_root / slug
        if target.exists():
            moved_items += _move_tree_merge(entry, target)
        else:
            shutil.move(str(entry), str(target))
        consolidated += 1
    return {"consolidated": consolidated, "moved_items": moved_items}


def consolidate_duplicates(db: Session) -> dict[str, int]:
    ensure_base_folders()
    projects_root = safe_join(CLOUD_ROOT, CLOUD_PROJECTS_DIR)
    if not projects_root.exists():
        return {"projects_consolidated": 0, "hypotheses_consolidated": 0, "updated_records": 0, "updated_experiments": 0}

    projects_by_slug: dict[str, list[Path]] = {}
    for entry in projects_root.iterdir():
        if entry.is_dir():
            projects_by_slug.setdefault(_normalize_folder_slug(entry.name), []).append(entry)

    projects_consolidated = 0
    hypotheses_consolidated = 0
    updated_records = 0
    updated_experiments = 0

    for slug, dirs in projects_by_slug.items():
        if len(dirs) <= 1:
            continue
        dirs.sort(key=lambda p: p.name)
        canonical = next((path for path in dirs if path.name == slug), dirs[0])
        old_name = canonical.name
        if canonical.name != slug:
            target = projects_root / slug
            if target.exists():
                canonical = target
            else:
                shutil.move(str(canonical), str(target))
                canonical = target
            old_prefix = f"{CLOUD_PROJECTS_DIR}/{old_name}/"
            new_prefix = f"{CLOUD_PROJECTS_DIR}/{slug}/"
            for exp in db.scalars(select(models.Experiment)).all():
                if exp.drive_folder_path and exp.drive_folder_path.startswith(old_prefix):
                    exp.drive_folder_path = exp.drive_folder_path.replace(old_prefix, new_prefix, 1)
                    updated_experiments += 1
            for record in db.scalars(select(models.ExperimentRecord)).all():
                if record.drive_folder_path and record.drive_folder_path.startswith(old_prefix):
                    record.drive_folder_path = record.drive_folder_path.replace(old_prefix, new_prefix, 1)
                    updated_records += 1
            for project in db.scalars(select(models.CloudProject)).all():
                if project.folder_path and project.folder_path.startswith(old_prefix):
                    project.folder_path = project.folder_path.replace(old_prefix, new_prefix, 1)

        for duplicate in dirs:
            if duplicate == canonical:
                continue
            dup_prefix = f"{CLOUD_PROJECTS_DIR}/{duplicate.name}/"
            canonical_prefix = f"{CLOUD_PROJECTS_DIR}/{canonical.name}/"
            for exp in db.scalars(select(models.Experiment)).all():
                if exp.drive_folder_path and exp.drive_folder_path.startswith(dup_prefix):
                    exp.drive_folder_path = exp.drive_folder_path.replace(dup_prefix, canonical_prefix, 1)
                    updated_experiments += 1
            for record in db.scalars(select(models.ExperimentRecord)).all():
                if record.drive_folder_path and record.drive_folder_path.startswith(dup_prefix):
                    record.drive_folder_path = record.drive_folder_path.replace(dup_prefix, canonical_prefix, 1)
                    updated_records += 1
            for project in db.scalars(select(models.CloudProject)).all():
                if project.folder_path and project.folder_path.startswith(dup_prefix):
                    project.folder_path = project.folder_path.replace(dup_prefix, canonical_prefix, 1)
            _move_tree_merge(duplicate, canonical)
            if duplicate.exists():
                shutil.move(str(duplicate), str(_archive_path(duplicate.name)))
            projects_consolidated += 1

        hypotheses_dir = canonical / "Hypotheses"
        for entry in canonical.iterdir():
            if entry.is_dir() and entry.name.startswith("Hypotheses_dup"):
                hypotheses_dir.mkdir(parents=True, exist_ok=True)
                _move_tree_merge(entry, hypotheses_dir)
                if entry.exists():
                    shutil.move(str(entry), str(_archive_path(entry.name)))
                hypotheses_consolidated += 1

    db.commit()
    return {
        "projects_consolidated": projects_consolidated,
        "hypotheses_consolidated": hypotheses_consolidated,
        "updated_records": updated_records,
        "updated_experiments": updated_experiments,
    }


def get_or_create_project(db: Session, project_name: str) -> models.CloudProject:
    project_key = _normalize_project_key(project_name)
    existing = db.scalars(
        select(models.CloudProject).where(models.CloudProject.project_key == project_key)
    ).first()
    if existing:
        desired_folder = f"{CLOUD_PROJECTS_DIR}/{_slugify(project_key)}"
        if existing.folder_path != desired_folder:
            source = safe_join(CLOUD_ROOT, existing.folder_path)
            target = safe_join(CLOUD_ROOT, desired_folder)
            if source.exists():
                if target.exists():
                    _move_tree_merge(source, target)
                else:
                    shutil.move(str(source), str(target))
            existing.folder_path = desired_folder
        if existing.project_name != project_name:
            existing.project_name = project_name
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    folder_name = _slugify(project_key)
    folder_path = f"{CLOUD_PROJECTS_DIR}/{folder_name}"
    project = models.CloudProject(
        project_name=project_name.strip(),
        project_key=project_key,
        folder_path=folder_path,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def project_root(project: models.CloudProject) -> str:
    return project.folder_path


def hypothesis_root(project: models.CloudProject, experiment: models.Experiment) -> str:
    project_rel = project_root(project)
    existing_name = _extract_folder_segment(experiment.drive_folder_path, "H")
    folder_name = existing_name or _build_folder_name("H", experiment.id, _pick_hypothesis_title(experiment))
    return f"{project_rel}/Hypotheses/{folder_name}"


def record_root(project: models.CloudProject, record: models.ExperimentRecord, experiment: models.Experiment) -> str:
    hypothesis_rel = hypothesis_root(project, experiment)
    existing_name = _extract_folder_segment(record.drive_folder_path, "R")
    name = record.record_name or record.session_id or f"record-{record.id}"
    folder_name = existing_name or _build_folder_name("R", record.id, name)
    return f"{hypothesis_rel}/Records/{folder_name}"



def ensure_hypothesis_folder(db: Session, experiment: models.Experiment) -> models.Experiment:
    ensure_base_folders()
    project = get_or_create_project(db, experiment.project_name)
    target_rel = hypothesis_root(project, experiment)
    updated_rel = _rename_if_needed(experiment.drive_folder_path, target_rel)
    if experiment.drive_folder_path != updated_rel:
        experiment.drive_folder_path = updated_rel
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
    return experiment


def ensure_record_folder(db: Session, record: models.ExperimentRecord) -> models.ExperimentRecord:
    ensure_base_folders()
    experiment = db.get(models.Experiment, record.experiment_id)
    if not experiment:
        return record
    experiment = ensure_hypothesis_folder(db, experiment)
    project = get_or_create_project(db, experiment.project_name)
    base_rel = f"{hypothesis_root(project, experiment)}/Records"
    folder_name = _extract_folder_segment(record.drive_folder_path, "R") or _build_folder_name(
        "R",
        record.id,
        record.record_name or record.session_id or f"record-{record.id}",
    )
    desired_rel = _available_rel_path(base_rel, folder_name, record.drive_folder_path)
    updated_rel = _rename_if_needed(record.drive_folder_path, desired_rel)
    if record.drive_folder_path != updated_rel:
        record.drive_folder_path = updated_rel
        db.add(record)
        db.commit()
        db.refresh(record)
    return record


def archive_drive_path(rel_path: str | None) -> str | None:
    if not rel_path:
        return None
    ensure_base_folders()
    source = safe_join(CLOUD_ROOT, rel_path)
    if not source.exists():
        return None
    target_base = Path("_Archived") / Path(rel_path).name
    target_rel = _available_rel_path("_Archived", target_base.name)
    target = safe_join(CLOUD_ROOT, target_rel)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    return target_rel


def bootstrap_base() -> dict[str, str]:
    ensure_base_folders()
    return {
        "system": str(safe_join(CLOUD_ROOT, "_System")),
        "projects": str(safe_join(CLOUD_ROOT, CLOUD_PROJECTS_DIR)),
        "archived": str(safe_join(CLOUD_ROOT, "_Archived")),
    }


def backfill_all(db: Session) -> dict[str, int]:
    ensure_base_folders()
    consolidation = _consolidate_legacy_projects()
    created = 0
    moved = 0
    updated = 0
    skipped = 0
    errors: list[str] = []

    for exp in db.scalars(select(models.Experiment)).all():
        before = exp.drive_folder_path
        if os.getenv("DRIVE_SYNC_DEBUG") == "1":
            logger.info(
                "drive-sync experiment=%s independent_variable=%s metric_x=%s hypothesis=%s",
                exp.id,
                exp.independent_variable,
                exp.metric_x,
                exp.hypothesis,
            )
        try:
            exp = ensure_hypothesis_folder(db, exp)
            if before is None and exp.drive_folder_path:
                created += 1
                updated += 1
            elif before != exp.drive_folder_path:
                moved += 1
                updated += 1
            else:
                skipped += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"experiment:{exp.id}:{exc}")

    for record in db.scalars(select(models.ExperimentRecord)).all():
        before = record.drive_folder_path
        try:
            record = ensure_record_folder(db, record)
            if before is None and record.drive_folder_path:
                created += 1
                updated += 1
            elif before != record.drive_folder_path:
                moved += 1
                updated += 1
            else:
                skipped += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"record:{record.id}:{exc}")

    return {
        "created": created,
        "project_consolidated": consolidation["consolidated"],
        "project_consolidated_items": consolidation["moved_items"],
        "moved": moved,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


def sync_hypothesis(db: Session, experiment_id: int) -> models.Experiment | None:
    exp = db.get(models.Experiment, experiment_id)
    if not exp:
        return None
    return ensure_hypothesis_folder(db, exp)


def sync_record(db: Session, record_id: int) -> models.ExperimentRecord | None:
    record = db.get(models.ExperimentRecord, record_id)
    if not record:
        return None
    return ensure_record_folder(db, record)
