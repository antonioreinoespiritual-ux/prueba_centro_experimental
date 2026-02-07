# app/routers/ai_analysis.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import ai, crud, schemas
from ..config import get_groq_model
from ..database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------ #
#  POST /ai/analyze/metrics/{entity_type}/{entity_id}
# ------------------------------------------------------------------ #

@router.post(
    "/analyze/metrics/{entity_type}/{entity_id}",
    response_model=schemas.AIAnalysisResponse,
)
def analyze_metrics(
    entity_type: schemas.EntityType,
    entity_id: int,
    db: Session = Depends(get_db),
):
    """AI analysis using ONLY quantitative metrics. No notes/documentation."""
    # Validate entity exists
    if entity_type == "experiment":
        exp = crud.get_experiment(db, entity_id)
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")
        evaluation = crud.evaluate_experiment(db, entity_id)
        records = crud.get_records(db, experiment_id=entity_id, limit=50000)
    elif entity_type == "record":
        rec = crud.get_record(db, entity_id)
        if not rec:
            raise HTTPException(status_code=404, detail="Record not found")
        exp = crud.get_experiment(db, rec.experiment_id)
        if not exp:
            raise HTTPException(status_code=404, detail="Parent experiment not found")
        evaluation = crud.evaluate_experiment(db, rec.experiment_id)
        records = [rec]
    else:
        raise HTTPException(status_code=400, detail="Invalid entity_type")

    try:
        output, input_snapshot = ai.generate_metrics_analysis(exp, evaluation, records)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ai.GroqError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    analysis = crud.create_ai_analysis(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        analysis_type="metrics",
        model=get_groq_model(),
        prompt_version=ai.METRICS_PROMPT_VERSION,
        input_snapshot=input_snapshot,
        output=output,
    )
    return schemas.AIAnalysisResponse(ai_analysis_id=analysis.id, output=output)


# ------------------------------------------------------------------ #
#  POST /ai/analyze/notes/{entity_type}/{entity_id}
# ------------------------------------------------------------------ #

@router.post(
    "/analyze/notes/{entity_type}/{entity_id}",
    response_model=schemas.AIAnalysisResponse,
)
def analyze_notes(
    entity_type: schemas.EntityType,
    entity_id: int,
    db: Session = Depends(get_db),
):
    """AI analysis using ONLY qualitative documentation/notes. No metrics."""
    # Validate entity exists
    if entity_type == "experiment":
        exp = crud.get_experiment(db, entity_id)
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")
    elif entity_type == "record":
        rec = crud.get_record(db, entity_id)
        if not rec:
            raise HTTPException(status_code=404, detail="Record not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid entity_type")

    documentation = crud.get_documentation(db, entity_type, entity_id)

    try:
        output, input_snapshot = ai.generate_notes_analysis(
            entity_type, entity_id, documentation,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ai.GroqError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    analysis = crud.create_ai_analysis(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        analysis_type="notes",
        model=get_groq_model(),
        prompt_version=ai.NOTES_PROMPT_VERSION,
        input_snapshot=input_snapshot,
        output=output,
    )
    return schemas.AIAnalysisResponse(ai_analysis_id=analysis.id, output=output)


# ------------------------------------------------------------------ #
#  POST /ai/analyze/combined/{entity_type}/{entity_id}
# ------------------------------------------------------------------ #

@router.post(
    "/analyze/combined/{entity_type}/{entity_id}",
    response_model=schemas.AIAnalysisResponse,
)
def analyze_combined(
    entity_type: schemas.EntityType,
    entity_id: int,
    db: Session = Depends(get_db),
):
    """AI analysis combining metrics + documentation + AI history."""
    focus_record = None
    record_doc = None
    record_ai_history = []

    if entity_type == "experiment":
        exp = crud.get_experiment(db, entity_id)
        if not exp:
            raise HTTPException(status_code=404, detail="Experiment not found")
        evaluation = crud.evaluate_experiment(db, entity_id)
        records = crud.get_records(db, experiment_id=entity_id, limit=50000)
        experiment_doc = crud.get_documentation(db, "experiment", entity_id)
        experiment_ai_history = crud.get_ai_analyses(db, "experiment", entity_id)
    elif entity_type == "record":
        focus_record = crud.get_record(db, entity_id)
        if not focus_record:
            raise HTTPException(status_code=404, detail="Record not found")
        exp = crud.get_experiment(db, focus_record.experiment_id)
        if not exp:
            raise HTTPException(status_code=404, detail="Parent experiment not found")
        evaluation = crud.evaluate_experiment(db, exp.id)
        records = crud.get_records(db, experiment_id=exp.id, limit=50000)
        experiment_doc = crud.get_documentation(db, "experiment", exp.id)
        experiment_ai_history = crud.get_ai_analyses(db, "experiment", exp.id)
        record_doc = crud.get_documentation(db, "record", focus_record.id)
        record_ai_history = crud.get_ai_analyses(db, "record", focus_record.id)
    else:
        raise HTTPException(status_code=400, detail="Invalid entity_type")

    try:
        output, input_snapshot = ai.generate_combined_analysis(
            experiment=exp,
            evaluation=evaluation,
            records=records,
            focus_record=focus_record,
            experiment_doc=experiment_doc,
            record_doc=record_doc,
            experiment_ai_history=experiment_ai_history,
            record_ai_history=record_ai_history,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ai.GroqError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    analysis = crud.create_ai_analysis(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        analysis_type="combined",
        model=get_groq_model(),
        prompt_version=ai.COMBINED_PROMPT_VERSION,
        input_snapshot=input_snapshot,
        output=output,
    )
    return schemas.AIAnalysisResponse(ai_analysis_id=analysis.id, output=output)


# ------------------------------------------------------------------ #
#  GET /ai/analysis/{entity_type}/{entity_id}
# ------------------------------------------------------------------ #

@router.get(
    "/analysis/{entity_type}/{entity_id}",
    response_model=list[schemas.AIAnalysisOut],
)
def list_analyses(
    entity_type: schemas.EntityType,
    entity_id: int,
    analysis_type: schemas.AIAnalysisType | None = None,
    db: Session = Depends(get_db),
):
    """List previous AI analyses for an entity, optionally filtered by type."""
    return crud.get_ai_analyses(db, entity_type, entity_id, analysis_type)
