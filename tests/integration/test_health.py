"""Integration tests for the application health endpoint."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ai_intake_triage.app import create_app
from ai_intake_triage.configuration.loader import BusinessConfigLoadError
from ai_intake_triage.configuration.settings import AppSettings

TEST_API_KEY = "0123456789abcdef0123456789abcdef"
TEST_SETTINGS = AppSettings(
    environment="test",
    operator_api_key=TEST_API_KEY,
    _env_file=None,
)


def test_health_check_returns_ok() -> None:
    """The public health endpoint reports that the application is running."""
    app = create_app(TEST_SETTINGS)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_interactive_documentation_is_disabled_in_test() -> None:
    """Non-development applications do not expose API documentation."""
    app = create_app(TEST_SETTINGS)

    with TestClient(app) as client:
        docs_response = client.get("/docs")
        schema_response = client.get("/openapi.json")

    assert docs_response.status_code == 404
    assert schema_response.status_code == 404


def test_application_loads_business_configuration() -> None:
    """Application creation loads the configured business rules."""
    app = create_app(TEST_SETTINGS)

    assert app.state.business_config.business.name == ("The Distracted Developer")
    assert len(app.state.business_config.services) == 5


def test_application_rejects_missing_business_configuration(
    tmp_path: Path,
) -> None:
    """Application creation fails when trusted configuration is unavailable."""
    settings = AppSettings(
        environment="test",
        operator_api_key=TEST_API_KEY,
        business_config_path=tmp_path / "missing.yaml",
        _env_file=None,
    )

    with pytest.raises(BusinessConfigLoadError):
        create_app(settings)
