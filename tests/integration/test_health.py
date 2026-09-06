"""Integration tests for the application health endpoint."""

from fastapi.testclient import TestClient

from ai_intake_triage.main import app


def test_health_check_returns_ok() -> None:
    """The public health endpoint reports that the application is running."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
