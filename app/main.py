# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from .config import load_env

load_env()

from .database import Base, engine
from .migrations import ensure_schema
from .routers import experiments, records, documentation, ai_analysis, publics, assistant, files, cloud
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

@app.get("/")
def home():
    return FileResponse(str(STATIC_DIR / "index.html"))

app.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
app.include_router(records.router, prefix="/records", tags=["records"])
app.include_router(documentation.router, prefix="/documentation", tags=["documentation"])
app.include_router(ai_analysis.router, prefix="/ai", tags=["ai-analysis"])
app.include_router(publics.router, prefix="/publics", tags=["publics"])
app.include_router(assistant.router, tags=["assistant"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(cloud.router, tags=["cloud"])
