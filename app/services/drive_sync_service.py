from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import os
import re
import shutil

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models


CLOUD_ROOT = Path(os.getenv("CLOUD_ROOT", "/Users/m2/CloudDriveData")).expanduser()
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DriveSyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0


def ensure_base_folders() -> None:
    for folder in ("_System", "Hypotheses", "Records", "_Archived"):
        (CLOUD_ROOT / folder).mkdir(parents=True, exist_ok=True)


def safe_join(root: Path, rel_path: str | None) -> Path:
    target = root / (rel_path or "")
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


def _build_folder_name(prefix: str, item_id: int, name: str) -> str:
    return f"{prefix}{item_id}_{_slugify(name)}"


def _available_rel_path(base_folder: str, folder_name: str, current_rel: str | None = None) -> str:
    base_path = Path(base_folder)
    candidate = base_path / folder_name
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
    if old_rel == new_rel:
        return new_rel
    old_path = safe_join(CLOUD_ROOT, old_rel) if old_rel else None
    new_path = safe_join(CLOUD_ROOT, new_rel)
    if old_path and old_path.exists():
        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_path), str(new_path))
    else:
        new_path.mkdir(parents=True, exist_ok=True)
    return new_rel


def _pick_hypothesis_title(experiment: models.Experiment) -> str:
    independent_variable = (experiment.independent_variable or "").strip()
    if independent_variable:
        return independent_variable
    metric_x = (experiment.metric_x or "").strip()
    if metric_x:
        return metric_x
    return "sin-variable"


def ensure_hypothesis_folder(db: Session, experiment: models.Experiment) -> models.Experiment:
    ensure_base_folders()
    title_source = _pick_hypothesis_title(experiment)
    slug = _slugify(title_source)
    target_rel = f"Hypotheses/H{experiment.id}_{slug}"
    updated_rel = _rename_if_needed(experiment.drive_folder_path, target_rel)
    if experiment.drive_folder_path != updated_rel:
        experiment.drive_folder_path = updated_rel
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
    return experiment


def ensure_record_folder(db: Session, record: models.ExperimentRecord) -> models.ExperimentRecord:
    ensure_base_folders()
    name = record.record_name or record.session_id or f"record-{record.id}"
    folder_name = _build_folder_name("R", record.id, name)
    desired_rel = _available_rel_path("Records", folder_name, record.drive_folder_path)
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
        "hypotheses": str(safe_join(CLOUD_ROOT, "Hypotheses")),
        "records": str(safe_join(CLOUD_ROOT, "Records")),
        "archived": str(safe_join(CLOUD_ROOT, "_Archived")),
    }


def backfill_all(db: Session) -> dict[str, int]:
    ensure_base_folders()
    created = 0
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
            elif before != exp.drive_folder_path:
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
            elif before != record.drive_folder_path:
                updated += 1
            else:
                skipped += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"record:{record.id}:{exc}")

    return {
        "created": created,
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
