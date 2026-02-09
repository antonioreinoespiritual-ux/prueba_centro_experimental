from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"

@router.get("/cloud")
def cloud_app():
    spa_index = STATIC_DIR / "cloud" / "index.html"
    legacy = STATIC_DIR / "cloud.html"
    if spa_index.exists():
        return FileResponse(str(spa_index))
    return FileResponse(str(legacy))
