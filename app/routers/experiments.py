# app/routers/experiments.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import ai, crud, schemas
from ..database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.ExperimentOut)
def create_experiment(experiment: schemas.ExperimentCreate, db: Session = Depends(get_db)):
    return crud.create_experiment(db, experiment)


@router.get("/", response_model=list[schemas.ExperimentOut])
def list_experiments(db: Session = Depends(get_db)):
    return crud.get_experiments(db)


@router.delete("/projects/{project_name}")
def delete_project(project_name: str, db: Session = Depends(get_db)):
    deleted_count = crud.delete_project(db, project_name)
    if not deleted_count:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"deleted": True, "project_name": project_name, "experiments_deleted": deleted_count}


@router.patch("/projects/{project_name}")
def rename_project(
    project_name: str,
    payload: schemas.ProjectRename,
    db: Session = Depends(get_db),
):
    new_project_name = payload.new_project_name.strip()
    if not new_project_name:
        raise HTTPException(status_code=400, detail="New project name is required")
    updated_count = crud.rename_project(db, project_name, new_project_name)
    if not updated_count:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "updated": True,
        "project_name": project_name,
        "new_project_name": new_project_name,
        "experiments_updated": updated_count,
    }


@router.get("/{experiment_id}", response_model=schemas.ExperimentOut)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    exp = crud.get_experiment(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.patch("/{experiment_id}", response_model=schemas.ExperimentOut)
def update_experiment(
    experiment_id: int,
    data: schemas.ExperimentUpdate,
    db: Session = Depends(get_db),
):
    exp = crud.update_experiment(db, experiment_id, data)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp


@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)):
    exp = crud.delete_experiment(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return {"deleted": True, "experiment_id": experiment_id}


@router.get("/{experiment_id}/evaluate", response_model=schemas.ExperimentEvaluation)
def evaluate_experiment(experiment_id: int, db: Session = Depends(get_db)):
    result = crud.evaluate_experiment(db, experiment_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return result


@router.post("/{experiment_id}/evaluate/apply", response_model=schemas.ExperimentOut)
def apply_evaluation(experiment_id: int, db: Session = Depends(get_db)):
    """Evaluate the hypothesis and auto-apply the suggested status if ready."""
    evaluation = crud.evaluate_experiment(db, experiment_id)
    if evaluation is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if not evaluation.ready_to_evaluate:
        raise HTTPException(
            status_code=400,
            detail="Experiment not ready to evaluate. Check volume and record statuses.",
        )
    if not evaluation.suggested_status:
        raise HTTPException(
            status_code=400,
            detail="Cannot determine status. Check threshold configuration.",
        )
    update_data = schemas.ExperimentUpdate(experiment_status=evaluation.suggested_status)
    return crud.update_experiment(db, experiment_id, update_data)


@router.get("/{experiment_id}/analysis", response_model=schemas.ExperimentAnalysis)
def analyze_experiment(experiment_id: int, db: Session = Depends(get_db)):
    exp = crud.get_experiment(db, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    evaluation = crud.evaluate_experiment(db, experiment_id)
    if evaluation is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    records = crud.get_records(db, experiment_id=experiment_id, limit=50000)
    try:
        analysis = ai.generate_experiment_analysis(exp, evaluation, records)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ai.GroqError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return schemas.ExperimentAnalysis(experiment_id=experiment_id, analysis=analysis)
