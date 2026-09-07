"""Unit tests for safe business-configuration loading."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from ai_intake_triage.configuration.loader import (
    BusinessConfigLoadError,
    load_business_config,
)


def test_missing_configuration_file_is_rejected(tmp_path: Path) -> None:
    """A missing configuration produces an application-specific error."""
    missing_path = tmp_path / "missing.yaml"

    with pytest.raises(
        BusinessConfigLoadError,
        match="Unable to read business configuration",
    ) as captured_error:
        load_business_config(missing_path)

    assert isinstance(captured_error.value.__cause__, FileNotFoundError)


def test_malformed_yaml_is_rejected(tmp_path: Path) -> None:
    """Invalid YAML cannot reach Pydantic validation."""
    config_path = tmp_path / "malformed.yaml"
    config_path.write_text("business: [", encoding="utf-8")

    with pytest.raises(
        BusinessConfigLoadError,
        match="contains invalid YAML",
    ) as captured_error:
        load_business_config(config_path)

    assert isinstance(captured_error.value.__cause__, yaml.YAMLError)


def test_non_mapping_document_is_rejected(tmp_path: Path) -> None:
    """The configuration document must contain a top-level mapping."""
    config_path = tmp_path / "list.yaml"
    config_path.write_text("- item\n- another item\n", encoding="utf-8")

    with pytest.raises(
        BusinessConfigLoadError,
        match="top-level mapping",
    ):
        load_business_config(config_path)


def test_schema_validation_failure_is_wrapped(tmp_path: Path) -> None:
    """Invalid configuration content preserves its validation cause."""
    config_path = tmp_path / "incomplete.yaml"
    config_path.write_text("version: '1.0'\n", encoding="utf-8")

    with pytest.raises(
        BusinessConfigLoadError,
        match="failed validation",
    ) as captured_error:
        load_business_config(config_path)

    assert isinstance(captured_error.value.__cause__, ValidationError)


def test_example_business_configuration_loads() -> None:
    """The repository's example configuration satisfies the trusted schema."""
    project_root = Path(__file__).resolve().parents[3]
    config_path = project_root / "configs" / "the_distracted_developer.yaml"

    config = load_business_config(config_path)

    assert config.version == "1.0.0"
    assert config.business.name == "The Distracted Developer"
    assert len(config.services) == 5
    assert len(config.intake_fields) == 15
    assert len(config.complexity.factors) == 9
