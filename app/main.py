# app/main.py
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .config import load_env

load_env()

from .database import Base, engine
from .migrations import ensure_schema
from .routers import experiments, records, documentation, ai_analysis, publics, publics_ui, assistant, files, cloud, drive_sync, hypotheses_ui, interviews, interviews_ui, clients, campaigns
ensure_schema()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Centro Experimental")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

def _serve_home() -> FileResponse:
    spa_index = STATIC_DIR / "home" / "index.html"
    legacy = STATIC_DIR / "index.html"
    if spa_index.exists():
        return FileResponse(str(spa_index), media_type="text/html")
    return FileResponse(str(legacy), media_type="text/html")


@app.get("/")
def home():
    return _serve_home()


@app.get("/create")
@app.get("/create/{path:path}")
def home_spa(path: str = ""):
    return _serve_home()


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/apple-touch-icon.png", include_in_schema=False)
def apple_touch_icon():
    return Response(status_code=204)


@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
def apple_touch_icon_precomposed():
    return Response(status_code=204)

app.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
app.include_router(records.router, prefix="/records", tags=["records"])
app.include_router(documentation.router, prefix="/documentation", tags=["documentation"])
app.include_router(ai_analysis.router, prefix="/ai", tags=["ai-analysis"])
app.include_router(publics.router, prefix="/publics", tags=["publics"])
app.include_router(publics_ui.router, tags=["publics-ui"])
app.include_router(assistant.router, tags=["assistant"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(cloud.router, tags=["cloud"])
app.include_router(drive_sync.router, tags=["drive-sync"])
app.include_router(hypotheses_ui.router, tags=["hypotheses-ui"])

app.include_router(interviews.router, tags=["interviews"])
app.include_router(interviews_ui.router, tags=["interviews-ui"])
app.include_router(clients.router, tags=["clients"])

app.include_router(campaigns.router, tags=["campaigns"])
