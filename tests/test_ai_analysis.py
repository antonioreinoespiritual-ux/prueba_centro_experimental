"""Tests for dual AI analysis (Metrics vs Notes) feature."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.main import app
from app.routers.ai_analysis import get_db

# ---------- Test DB setup ----------

TEST_DB_URL = "sqlite:///./data/test_ai_analysis.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


# Override DB dependency for all routers
from app.routers import experiments, records, documentation
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[experiments.get_db] = override_get_db
app.dependency_overrides[records.get_db] = override_get_db
app.dependency_overrides[documentation.get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ---------- Helpers ----------

def create_test_experiment():
    resp = client.post("/experiments/", json={
        "project_name": "Test AI Project",
        "hypothesis": "If we change X then Y improves",
        "traffic_type": "paid",
        "hypothesis_type": "acquisition",
        "primary_metric": "ctr",
        "threshold_operator": ">=",
        "threshold_value": 3.0,
        "threshold_type": "percentage",
        "volume_min_value": 100,
        "volume_unit": "views",
        "contexto": "Este es el contexto inicial del experimento para pruebas.",
    })
    assert resp.status_code == 200
    return resp.json()


def create_test_record(experiment_id: int):
    resp = client.post("/records/", json={
        "experiment_id": experiment_id,
        "session_id": "test-session-001",
        "clicks": 50,
        "views": 1000,
        "ctr": 5.0,
        "execution_type": "paid_ad",
        "record_name": "Test Record A",
        "contexto_record": "Nota cualitativa del record para pruebas.",
    })
    assert resp.status_code == 200
    return resp.json()


MOCK_AI_RESPONSE = {
    "choices": [{
        "message": {
            "content": "**Fuente usada: Métricas**\n\nAnálisis de prueba generado.\n\nNo asumí documentación cualitativa."
        }
    }]
}

MOCK_AI_RESPONSE_NOTES = {
    "choices": [{
        "message": {
            "content": "**Fuente usada: Documentación**\n\nSíntesis cualitativa de prueba.\n\nNo usé métricas cuantitativas."
        }
    }]
}


def mock_groq_post(*args, **kwargs):
    """Mock Groq API responses based on the prompt content."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    payload = kwargs.get("json", {})
    messages = payload.get("messages", [])
    system_msg = messages[0]["content"] if messages else ""
    if "analista cualitativo senior" in system_msg:
        mock_resp.text = json.dumps(MOCK_AI_RESPONSE_NOTES)
    else:
        mock_resp.text = json.dumps(MOCK_AI_RESPONSE)
    return mock_resp


# ---------- Tests ----------

class TestAIAnalysisMetrics:
    """Tests for POST /ai/analyze/metrics/{entity_type}/{entity_id}"""

    @patch("app.ai.requests.post", side_effect=mock_groq_post)
    @patch("app.ai.get_groq_api_key", return_value="test-key")
    def test_metrics_analysis_experiment(self, mock_key, mock_post):
        exp = create_test_experiment()
        rec = create_test_record(exp["id"])

        resp = client.post(f"/ai/analyze/metrics/experiment/{exp['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert "ai_analysis_id" in data
        assert "output" in data
        assert "Fuente usada: Métricas" in data["output"]
        assert "No asumí documentación cualitativa" in data["output"]

    @patch("app.ai.requests.post", side_effect=mock_groq_post)
    @patch("app.ai.get_groq_api_key", return_value="test-key")
    def test_metrics_analysis_record(self, mock_key, mock_post):
        exp = create_test_experiment()
        rec = create_test_record(exp["id"])

        resp = client.post(f"/ai/analyze/metrics/record/{rec['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert "Fuente usada: Métricas" in data["output"]

    @patch("app.ai.requests.post", side_effect=mock_groq_post)
    @patch("app.ai.get_groq_api_key", return_value="test-key")
    def test_metrics_input_excludes_notes(self, mock_key, mock_post):
        """Verify that the metrics endpoint does NOT send notes/qualitative data."""
        exp = create_test_experiment()
        create_test_record(exp["id"])

        resp = client.post(f"/ai/analyze/metrics/experiment/{exp['id']}")
        assert resp.status_code == 200

        # Check the actual call to Groq - the input should not contain notes
        call_args = mock_post.call_args
        payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1]
        user_message = payload["messages"][1]["content"]
        assert "nota" not in user_message.lower() or "contexto inicial" not in user_message.lower()
        # The input should contain metrics data
        assert "metrics" in user_message.lower() or "aggregated" in user_message.lower()

    def test_metrics_analysis_not_found(self):
        resp = client.post("/ai/analyze/metrics/experiment/99999")
        assert resp.status_code == 404


class TestAIAnalysisNotes:
    """Tests for POST /ai/analyze/notes/{entity_type}/{entity_id}"""

    @patch("app.ai.requests.post", side_effect=mock_groq_post)
    @patch("app.ai.get_groq_api_key", return_value="test-key")
    def test_notes_analysis_experiment(self, mock_key, mock_post):
        exp = create_test_experiment()

        resp = client.post(f"/ai/analyze/notes/experiment/{exp['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert "ai_analysis_id" in data
        assert "output" in data
        assert "Fuente usada: Documentación" in data["output"]
        assert "No usé métricas cuantitativas" in data["output"]

    @patch("app.ai.requests.post", side_effect=mock_groq_post)
    @patch("app.ai.get_groq_api_key", return_value="test-key")
    def test_notes_analysis_record(self, mock_key, mock_post):
        exp = create_test_experiment()
        rec = create_test_record(exp["id"])

        resp = client.post(f"/ai/analyze/notes/record/{rec['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert "Fuente usada: Documentación" in data["output"]

    @patch("app.ai.requests.post", side_effect=mock_groq_post)
    @patch("app.ai.get_groq_api_key", return_value="test-key")
    def test_notes_input_excludes_metrics(self, mock_key, mock_post):
        """Verify that the notes endpoint does NOT send metrics data."""
        exp = create_test_experiment()
        create_test_record(exp["id"])

        resp = client.post(f"/ai/analyze/notes/experiment/{exp['id']}")
        assert resp.status_code == 200

        call_args = mock_post.call_args
        payload = call_args[1]["json"] if "json" in call_args[1] else call_args[0][1]
        user_message = payload["messages"][1]["content"]
        # Notes input should NOT contain metrics like threshold, volume, aggregated
        assert "threshold" not in user_message.lower()
        assert "aggregated" not in user_message.lower()
        assert "volume_sufficient" not in user_message.lower()

    def test_notes_analysis_not_found(self):
        resp = client.post("/ai/analyze/notes/experiment/99999")
        assert resp.status_code == 404


class TestAIAnalysisHistory:
    """Tests for GET /ai/analysis/{entity_type}/{entity_id}"""

    @patch("app.ai.requests.post", side_effect=mock_groq_post)
    @patch("app.ai.get_groq_api_key", return_value="test-key")
    def test_list_analyses(self, mock_key, mock_post):
        exp = create_test_experiment()
        create_test_record(exp["id"])

        # Create both types of analysis
        client.post(f"/ai/analyze/metrics/experiment/{exp['id']}")
        client.post(f"/ai/analyze/notes/experiment/{exp['id']}")

        # List all
        resp = client.get(f"/ai/analysis/experiment/{exp['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2

        # Filter by type
        resp_metrics = client.get(f"/ai/analysis/experiment/{exp['id']}?analysis_type=metrics")
        assert resp_metrics.status_code == 200
        for item in resp_metrics.json():
            assert item["analysis_type"] == "metrics"

        resp_notes = client.get(f"/ai/analysis/experiment/{exp['id']}?analysis_type=notes")
        assert resp_notes.status_code == 200
        for item in resp_notes.json():
            assert item["analysis_type"] == "notes"

    @patch("app.ai.requests.post", side_effect=mock_groq_post)
    @patch("app.ai.get_groq_api_key", return_value="test-key")
    def test_analysis_persistence(self, mock_key, mock_post):
        """Verify analyses are persisted with input_snapshot for reproducibility."""
        exp = create_test_experiment()
        create_test_record(exp["id"])

        client.post(f"/ai/analyze/metrics/experiment/{exp['id']}")

        resp = client.get(f"/ai/analysis/experiment/{exp['id']}?analysis_type=metrics")
        data = resp.json()
        assert len(data) >= 1
        latest = data[0]
        assert latest["entity_type"] == "experiment"
        assert latest["entity_id"] == exp["id"]
        assert latest["analysis_type"] == "metrics"
        assert latest["model"]  # model recorded
        assert latest["prompt_version"]  # prompt version recorded
        assert latest["input_snapshot"]  # input snapshot recorded
        assert latest["output"]  # output recorded

        # Verify input_snapshot is valid JSON
        snapshot = json.loads(latest["input_snapshot"])
        assert "experiment" in snapshot
        assert "records" in snapshot


class TestAIAnalysisSecurity:
    """Security tests to verify source isolation."""

    @patch("app.ai.requests.post", side_effect=mock_groq_post)
    @patch("app.ai.get_groq_api_key", return_value="test-key")
    def test_metrics_endpoint_no_notes_in_snapshot(self, mock_key, mock_post):
        """Metrics analysis input_snapshot must NOT contain notes."""
        exp = create_test_experiment()
        create_test_record(exp["id"])
        # Add extra notes
        client.post(f"/documentation/experiment/{exp['id']}/notes", json={"body": "Secret qualitative note"})

        client.post(f"/ai/analyze/metrics/experiment/{exp['id']}")

        resp = client.get(f"/ai/analysis/experiment/{exp['id']}?analysis_type=metrics")
        latest = resp.json()[0]
        snapshot = json.loads(latest["input_snapshot"])

        # No notes key in snapshot
        assert "notes" not in snapshot
        assert "body" not in json.dumps(snapshot)
        assert "Secret qualitative note" not in json.dumps(snapshot)

    @patch("app.ai.requests.post", side_effect=mock_groq_post)
    @patch("app.ai.get_groq_api_key", return_value="test-key")
    def test_notes_endpoint_no_metrics_in_snapshot(self, mock_key, mock_post):
        """Notes analysis input_snapshot must NOT contain metrics."""
        exp = create_test_experiment()
        create_test_record(exp["id"])

        client.post(f"/ai/analyze/notes/experiment/{exp['id']}")

        resp = client.get(f"/ai/analysis/experiment/{exp['id']}?analysis_type=notes")
        latest = resp.json()[0]
        snapshot = json.loads(latest["input_snapshot"])

        # No metrics in snapshot
        assert "threshold" not in snapshot
        assert "aggregated" not in json.dumps(snapshot)
        assert "volume_sufficient" not in json.dumps(snapshot)
        assert "clicks" not in json.dumps(snapshot)
