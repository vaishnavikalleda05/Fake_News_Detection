"""Integration and unit tests for FastAPI backend and ML integration."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.ml_service import MLService


@pytest.fixture(scope="module")
def client() -> TestClient:
    """TestClient fixture that triggers lifespan events to load the model."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client: TestClient) -> None:
    """Root endpoint should return 200 with service metadata and documentation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "docs_url" in data
    assert data["docs_url"] == "/docs"


def test_health_endpoint(client: TestClient) -> None:
    """Health check should return 200, healthy status, and true model loaded flag."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Fake News Detection API"
    assert data["ml_model_loaded"] is True
    assert "version" in data


def test_analyze_ml_only_with_both_headline_and_body(client: TestClient) -> None:
    """Analyze endpoint with headline and body text should classify successfully."""
    payload = {
        "headline": "Federal Reserve signals gradual adjustment to economic monetary policy",
        "article_text": "WASHINGTON (Reuters) - Central bankers outlined their baseline projections for the upcoming fiscal quarter.",
    }
    response = client.post("/api/analyze/ml-only", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in {"FAKE", "REAL"}
    assert 0.0 <= data["confidence"] <= 1.0
    assert 0.0 <= data["prob_fake"] <= 1.0
    assert data["model"] == "TF-IDF + Logistic Regression"
    assert data["char_count"] > 0
    assert data["word_count"] > 0
    assert "analyzed_at" in data


def test_analyze_ml_only_with_headline_only(client: TestClient) -> None:
    """Analyze endpoint with headline only should work."""
    payload = {"headline": "Viral miracle cure claims rejected by medical authorities"}
    response = client.post("/api/analyze/ml-only", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in {"FAKE", "REAL"}
    assert 0.0 <= data["confidence"] <= 1.0


def test_analyze_ml_only_with_article_text_only(client: TestClient) -> None:
    """Analyze endpoint with article text only should work."""
    payload = {
        "article_text": "Government committee votes to pass the annual infrastructure budget with bipartisan backing."
    }
    response = client.post("/api/analyze/ml-only", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"] in {"FAKE", "REAL"}
    assert 0.0 <= data["confidence"] <= 1.0


def test_analyze_ml_only_empty_payload_fails(client: TestClient) -> None:
    """Analyze endpoint must reject empty strings or whitespace-only inputs."""
    payload = {"headline": "   ", "article_text": ""}
    response = client.post("/api/analyze/ml-only", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_ml_service_predict_unloaded_raises_error() -> None:
    """MLService should cleanly raise error when model is not loaded."""
    service = MLService(model_path=Path("non_existent_model_path.joblib"))
    assert service.is_loaded is False
    with pytest.raises(RuntimeError) as exc_info:
        service.predict(headline="Test headline")
    assert "ML model is not loaded" in str(exc_info.value)
    