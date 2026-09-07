"""Unit tests for business-configuration models."""

from typing import Any

import pytest
from pydantic import ValidationError

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import ServiceMatchLevel


def valid_configuration() -> dict[str, Any]:
    """Return a minimal valid business configuration."""
    return {
        "version": "1.0",
        "business": {
            "name": "The Distracted Developer",
            "description": "Practical software and automation services.",
        },
        "intake_fields": [
            {
                "id": "current_systems",
                "description": "Systems currently used in the workflow.",
                "default_question": "Which systems do you currently use?",
            },
            {
                "id": "processing_volume",
                "description": "Approximate items processed over time.",
                "default_question": (
                    "Approximately how many items do you process each month?"
                ),
            },
        ],
        "services": [
            {
                "id": "workflow_automation",
                "name": "Workflow Automation",
                "description": "Automation across business systems.",
                "typical_capabilities": [
                    "system integration",
                    "data validation",
                ],
                "required_information": ["current_systems"],
                "optional_information": ["processing_volume"],
                "base_complexity_points": 1,
            }
        ],
        "supported_technologies": ["Python", "FastAPI"],
        "complexity": {
            "factors": [
                {
                    "id": "multiple_external_systems",
                    "description": "Three or more external systems are involved.",
                    "points": 2,
                }
            ],
            "thresholds": {
                "low_max": 2,
                "medium_max": 5,
            },
        },
        "routing": {
            "discovery_match_levels": ["strong", "possible"],
        },
    }


def test_valid_business_configuration_is_accepted() -> None:
    """A complete internally consistent configuration is accepted."""
    config = BusinessConfig.model_validate(valid_configuration())

    assert config.business.name == "The Distracted Developer"
    assert config.services[0].id == "workflow_automation"
    assert config.routing.discovery_match_levels == [
        ServiceMatchLevel.STRONG,
        ServiceMatchLevel.POSSIBLE,
    ]


def test_duplicate_catalog_ids_are_rejected() -> None:
    """Catalog IDs must remain unique for deterministic references."""
    config_data = valid_configuration()
    config_data["intake_fields"].append(config_data["intake_fields"][0])

    with pytest.raises(ValidationError, match="duplicate IDs"):
        BusinessConfig.model_validate(config_data)


def test_unknown_intake_field_reference_is_rejected() -> None:
    """Services cannot reference fields absent from the shared catalog."""
    config_data = valid_configuration()
    config_data["services"][0]["required_information"].append("unknown_field")

    with pytest.raises(ValidationError, match="unknown intake field IDs"):
        BusinessConfig.model_validate(config_data)


def test_required_and_optional_overlap_is_rejected() -> None:
    """One service cannot assign both priorities to the same field."""
    config_data = valid_configuration()
    config_data["services"][0]["optional_information"].append("current_systems")

    with pytest.raises(
        ValidationError,
        match="both required and optional",
    ):
        BusinessConfig.model_validate(config_data)


def test_complexity_thresholds_must_increase() -> None:
    """Low and medium score ranges cannot overlap."""
    config_data = valid_configuration()
    config_data["complexity"]["thresholds"] = {
        "low_max": 5,
        "medium_max": 5,
    }

    with pytest.raises(ValidationError, match="low_max must be less"):
        BusinessConfig.model_validate(config_data)


def test_weak_match_cannot_be_eligible_for_discovery() -> None:
    """Weak service matches always require manual assessment."""
    config_data = valid_configuration()
    config_data["routing"]["discovery_match_levels"].append("weak")

    with pytest.raises(ValidationError, match="weak service match"):
        BusinessConfig.model_validate(config_data)


def test_unknown_configuration_fields_are_rejected() -> None:
    """Misspelled or unsupported fields cannot be silently ignored."""
    config_data = valid_configuration()
    config_data["bussiness"] = {}

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        BusinessConfig.model_validate(config_data)
