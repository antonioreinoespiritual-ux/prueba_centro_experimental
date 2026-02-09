from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path


BASE_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"
MAX_UPLOAD_BYTES = 3 * 1024 * 1024 * 1024


def ensure_upload_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sanitize_filename(filename: str | None) -> str:
    if not filename:
        return "archivo"
    name = Path(filename).name.strip()
    if not name:
        return "archivo"
    return name[:255]


def _clean_segment(segment: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9 _.-]", "_", segment).strip()
    return cleaned[:100]


def normalize_folder(folder: str | None) -> str | None:
    if not folder:
        return None
    folder = folder.replace("\\", "/").strip()
    parts: list[str] = []
    for raw in folder.split("/"):
        raw = raw.strip()
        if not raw or raw in {".", ".."}:
            continue
        cleaned = _clean_segment(raw)
        if cleaned:
            parts.append(cleaned)
    return "/".join(parts) if parts else None


def build_stored_name(display_name: str) -> str:
    suffix = Path(display_name).suffix
    return f"{uuid.uuid4().hex}{suffix}"


def build_entity_folder(entity_type: str, entity_id: int, folder: str | None = None) -> Path:
    base = BASE_UPLOAD_DIR / entity_type / str(entity_id)
    if folder:
        return base / folder
    return base


def build_file_path(entity_type: str, entity_id: int, stored_name: str, folder: str | None = None) -> Path:
    return build_entity_folder(entity_type, entity_id, folder) / stored_name


def remove_entity_files(entity_type: str, entity_id: int) -> None:
    root = build_entity_folder(entity_type, entity_id)
    if root.exists():
        shutil.rmtree(root)


def remove_file(path: Path) -> None:
    if path.exists():
        path.unlink()
