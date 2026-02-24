from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse
from pathlib import Path

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"


@router.get("/hypotheses")
def hypotheses_app():
    spa_index = STATIC_DIR / "hypotheses" / "index.html"
    legacy = STATIC_DIR / "hypotheses.html"
    if spa_index.exists():
        return FileResponse(str(spa_index))
    return FileResponse(str(legacy))


@router.get("/hypotheses/{path:path}")
def hypotheses_spa_fallback(path: str):
    spa_index = STATIC_DIR / "hypotheses" / "index.html"
    if spa_index.exists():
        return FileResponse(str(spa_index))
    return RedirectResponse(url="/hypotheses", status_code=307)


@router.get("/static/hypotheses.html")
def hypotheses_legacy_redirect():
    return RedirectResponse(url="/hypotheses", status_code=307)
