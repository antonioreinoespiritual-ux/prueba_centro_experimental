from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models
from app.services import drive_sync_service


TEST_DB_URL = "sqlite:///./data/test_cloud_projects.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def _set_cloud_root(tmp_path: Path) -> None:
    drive_sync_service.CLOUD_ROOT = tmp_path


def test_project_grouping_single_cloud_project(tmp_path: Path):
    _set_cloud_root(tmp_path)
    db = TestSession()
    try:
        project_name = "Atracción  inversa"
        experiments = []
        for idx in range(3):
            exp = models.Experiment(
                project_name=project_name,
                hypothesis=f"hipotesis {idx}",
                traffic_type="paid",
            )
            db.add(exp)
            db.commit()
            db.refresh(exp)
            experiments.append(exp)
            drive_sync_service.ensure_hypothesis_folder(db, exp)

        projects = db.query(models.CloudProject).all()
        assert len(projects) == 1
    finally:
        db.close()


def test_records_under_hypothesis(tmp_path: Path):
    _set_cloud_root(tmp_path)
    db = TestSession()
    try:
        exp = models.Experiment(
            project_name="Atracción inversa",
            hypothesis="hipotesis principal",
            traffic_type="paid",
            independent_variable="Variable X",
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)
        drive_sync_service.ensure_hypothesis_folder(db, exp)

        record = models.ExperimentRecord(
            experiment_id=exp.id,
            session_id="session-1",
            record_name="Record A",
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        drive_sync_service.ensure_record_folder(db, record)

        project_key = drive_sync_service._normalize_project_key(exp.project_name)
        project_slug = drive_sync_service._slugify(project_key)
        assert record.drive_folder_path is not None
        assert record.drive_folder_path.startswith(
            f"Projects/{project_slug}/Hypotheses/H{exp.id}_"
        )
        assert "/Records/R" in record.drive_folder_path
    finally:
        db.close()
