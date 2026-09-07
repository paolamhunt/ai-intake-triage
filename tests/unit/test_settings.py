"""Unit tests for application settings."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_intake_triage.configuration.settings import AppSettings

VALID_API_KEY = "0123456789abcdef0123456789abcdef"


def test_operator_api_key_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    """Application settings reject a missing operator API key."""
    monkeypatch.delenv("AIT_OPERATOR_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


def test_operator_api_key_requires_minimum_length() -> None:
    """Application settings reject an insufficiently long API key."""
    with pytest.raises(ValidationError):
        AppSettings(operator_api_key="too-short", _env_file=None)


@pytest.mark.parametrize(
    ("environment", "expected"),
    [
        ("development", True),
        ("test", False),
        ("production", False),
    ],
)
def test_documentation_is_limited_to_development(
    environment: str,
    expected: bool,
) -> None:
    """Interactive documentation is enabled only in development."""
    settings = AppSettings(
        environment=environment,
        operator_api_key=VALID_API_KEY,
        _env_file=None,
    )

    assert settings.documentation_enabled is expected


def test_operator_api_key_is_masked() -> None:
    """Settings do not reveal the API key through normal string conversion."""
    settings = AppSettings(
        operator_api_key=VALID_API_KEY,
        _env_file=None,
    )

    assert str(settings.operator_api_key) == "**********"


def test_default_business_configuration_path() -> None:
    """Settings use the example business configuration by default."""
    settings = AppSettings(
        operator_api_key=VALID_API_KEY,
        _env_file=None,
    )

    assert settings.business_config_path == Path(
        "configs/the_distracted_developer.yaml"
    )


def test_business_configuration_path_can_be_overridden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A deployment can select another trusted configuration file."""
    monkeypatch.setenv(
        "AIT_BUSINESS_CONFIG_PATH",
        "configs/another_business.yaml",
    )

    settings = AppSettings(
        operator_api_key=VALID_API_KEY,
        _env_file=None,
    )

    assert settings.business_config_path == Path("configs/another_business.yaml")
