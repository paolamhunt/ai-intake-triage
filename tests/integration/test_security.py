"""Integration tests for operator API-key authentication."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from ai_intake_triage.api.security import build_operator_auth
from ai_intake_triage.configuration.settings import AppSettings

VALID_API_KEY = "0123456789abcdef0123456789abcdef"
TEST_SETTINGS = AppSettings(
    environment="test",
    operator_api_key=VALID_API_KEY,
    _env_file=None,
)


def create_protected_test_app() -> FastAPI:
    """Create a minimal application using the real authentication dependency."""
    app = FastAPI()
    operator_auth = build_operator_auth(TEST_SETTINGS)

    @app.get("/protected", dependencies=[Depends(operator_auth)])
    def protected_route() -> dict[str, str]:
        return {"status": "authorized"}

    return app


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"X-API-Key": "incorrect-api-key"},
    ],
)
def test_protected_route_rejects_invalid_credentials(
    headers: dict[str, str],
) -> None:
    """Missing and incorrect API keys receive the same safe response."""
    app = create_protected_test_app()

    with TestClient(app) as client:
        response = client.get("/protected", headers=headers)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key."}


def test_protected_route_accepts_configured_api_key() -> None:
    """The configured operator API key grants access."""
    app = create_protected_test_app()

    with TestClient(app) as client:
        response = client.get(
            "/protected",
            headers={"X-API-Key": VALID_API_KEY},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "authorized"}
