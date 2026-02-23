from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["publics-ui"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"


@router.get("/publics-app")
def publics_app():
    return FileResponse(str(STATIC_DIR / "publics.html"), media_type="text/html")
