"""Tests for deterministic preliminary complexity assessment."""

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.complexity import assess_complexity
from ai_intake_triage.domain.enums import ComplexityLevel
from ai_intake_triage.domain.extraction import (
    AIExtraction,
    ComplexityFactorCandidate,
    IntakeFieldFinding,
    ServiceCandidate,
)


def make_business_config() -> BusinessConfig:
    """Build a configuration with useful scoring boundaries."""
    return BusinessConfig.model_validate(
        {
            "version": "1.0.0",
            "business": {
                "name": "Example Consulting",
                "description": "An example service business.",
            },
            "intake_fields": [
                {
                    "id": "project_goal",
                    "description": "What the client wants to achieve.",
                    "default_question": "What outcome are you hoping to achieve?",
                },
                {
                    "id": "monthly_volume",
                    "description": "How much work is processed.",
                    "default_question": "How many items are processed each month?",
                },
            ],
            "services": [
                {
                    "id": "workflow_automation",
                    "name": "Workflow Automation",
                    "description": "Automation of repetitive workflows.",
                    "typical_capabilities": ["Process automation"],
                    "required_information": ["project_goal", "monthly_volume"],
                    "base_complexity_points": 2,
                },
                {
                    "id": "custom_application",
                    "name": "Custom Application",
                    "description": "Development of a custom application.",
                    "typical_capabilities": ["Application development"],
                    "required_information": ["project_goal"],
                    "base_complexity_points": 5,
                },
            ],
            "complexity": {
                "factors": [
                    {
                        "id": "external_integration",
                        "description": "Requires an external integration.",
                        "points": 3,
                    },
                    {
                        "id": "sensitive_data",
                        "description": "Processes sensitive data.",
                        "points": 5,
                    },
                ],
                "thresholds": {"low_max": 3, "medium_max": 8},
            },
            "routing": {"discovery_match_levels": ["strong", "possible"]},
        }
    )


def extraction(**updates: object) -> AIExtraction:
    """Build an extraction with required provider fields."""
    return AIExtraction(
        summary="The client wants assistance.",
        primary_pain_point="Manual work",
        **updates,
    )


def candidate(service_id: str, match_level: str = "strong") -> ServiceCandidate:
    """Build a service candidate."""
    return ServiceCandidate(
        service_id=service_id,
        match_level=match_level,
        reason=f"The inquiry may match {service_id}.",
        evidence=["client request"],
    )


def factor(factor_id: str) -> ComplexityFactorCandidate:
    """Build a complexity-factor candidate."""
    return ComplexityFactorCandidate(
        factor_id=factor_id,
        reason=f"The inquiry indicates {factor_id}.",
        evidence=["client request"],
    )


def test_returns_unknown_without_validated_service_candidate() -> None:
    result = assess_complexity(extraction(), make_business_config())

    assert result.level is ComplexityLevel.UNKNOWN
    assert result.score is None
    assert result.factors == []
    assert result.unknowns == ["service_classification"]


def test_uses_best_candidate_base_score_and_configured_threshold() -> None:
    result = assess_complexity(
        extraction(
            service_candidates=[
                candidate("custom_application", "possible"),
                candidate("workflow_automation", "strong"),
            ]
        ),
        make_business_config(),
    )

    assert result.level is ComplexityLevel.LOW
    assert result.score == 2


def test_adds_configured_factor_points_to_reach_medium() -> None:
    integration = factor("external_integration")

    result = assess_complexity(
        extraction(
            service_candidates=[candidate("workflow_automation")],
            complexity_factors=[integration],
        ),
        make_business_config(),
    )

    assert result.level is ComplexityLevel.MEDIUM
    assert result.score == 5
    assert result.factors == [integration]


def test_assigns_high_above_medium_threshold() -> None:
    result = assess_complexity(
        extraction(
            service_candidates=[candidate("custom_application")],
            complexity_factors=[
                factor("external_integration"),
                factor("sensitive_data"),
            ],
        ),
        make_business_config(),
    )

    assert result.level is ComplexityLevel.HIGH
    assert result.score == 13


def test_records_missing_required_fields_without_hiding_preliminary_score() -> None:
    result = assess_complexity(
        extraction(
            service_candidates=[candidate("workflow_automation")],
            intake_field_findings=[
                IntakeFieldFinding(
                    field_id="project_goal",
                    value="Reduce manual invoice processing",
                    evidence=["invoice processing"],
                )
            ],
        ),
        make_business_config(),
    )

    assert result.level is ComplexityLevel.LOW
    assert result.score == 2
    assert result.unknowns == ["monthly_volume"]
