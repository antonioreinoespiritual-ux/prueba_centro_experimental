from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"


@router.get("/interviews")
def interviews_app():
    spa_index = STATIC_DIR / "interviews" / "index.html"
    if spa_index.exists():
        return FileResponse(str(spa_index))
    return FileResponse(str(STATIC_DIR / "index.html"))
