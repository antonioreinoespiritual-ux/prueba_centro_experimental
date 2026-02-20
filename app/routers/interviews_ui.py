from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"


def _serve_interviews_index() -> FileResponse:
    spa_index = STATIC_DIR / "interviews" / "index.html"
    if spa_index.exists():
        return FileResponse(str(spa_index), media_type="text/html")
    return FileResponse(str(STATIC_DIR / "index.html"), media_type="text/html")


@router.get("/interviews")
def interviews_app():
    return _serve_interviews_index()


@router.get("/interviews/{path:path}")
def interviews_spa_fallback(path: str):
    return _serve_interviews_index()
