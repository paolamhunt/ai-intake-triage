"""Tests for validation of AI extraction references to business configuration."""

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import ValidationIssueCode
from ai_intake_triage.domain.extraction import (
    AIExtraction,
    ComplexityFactorCandidate,
    DraftClarifyingQuestion,
    IntakeFieldFinding,
    ServiceCandidate,
)
from ai_intake_triage.domain.extraction_validation import (
    validate_extraction_references,
)


def make_business_config() -> BusinessConfig:
    """Build the smallest valid configuration needed by these tests."""
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
                }
            ],
            "services": [
                {
                    "id": "workflow_automation",
                    "name": "Workflow Automation",
                    "description": "Automation of repetitive business workflows.",
                    "typical_capabilities": ["Process automation"],
                    "required_information": ["project_goal"],
                    "base_complexity_points": 1,
                }
            ],
            "supported_technologies": ["Email"],
            "complexity": {
                "factors": [
                    {
                        "id": "external_integration",
                        "description": "Requires an external system integration.",
                        "points": 2,
                    }
                ],
                "thresholds": {"low_max": 3, "medium_max": 8},
            },
            "routing": {"discovery_match_levels": ["strong", "possible"]},
        }
    )


def make_extraction(**updates: object) -> AIExtraction:
    """Build an extraction with required fields and selected candidates."""
    return AIExtraction(
        summary="The client wants help with a repetitive workflow.",
        primary_pain_point="Manual processing",
        **updates,
    )


def test_keeps_candidates_that_reference_configured_ids() -> None:
    extraction = make_extraction(
        intake_field_findings=[
            IntakeFieldFinding(
                field_id="project_goal",
                value="Automate invoice handling",
                evidence=["automate invoice handling"],
            )
        ],
        service_candidates=[
            ServiceCandidate(
                service_id="workflow_automation",
                match_level="strong",
                reason="The inquiry describes a repetitive workflow.",
                evidence=["repetitive workflow"],
            )
        ],
        complexity_factors=[
            ComplexityFactorCandidate(
                factor_id="external_integration",
                reason="The workflow uses email.",
                evidence=["uses email"],
            )
        ],
        draft_questions=[
            DraftClarifyingQuestion(
                field_id="project_goal",
                question="What outcome are you hoping to achieve?",
            )
        ],
    )

    result = validate_extraction_references(extraction, make_business_config())

    assert result.extraction == extraction
    assert result.validation_issues == []


def test_rejects_candidates_that_reference_unknown_ids() -> None:
    extraction = make_extraction(
        intake_field_findings=[
            IntakeFieldFinding(
                field_id="invented_field",
                value="An unsupported value",
                evidence=["unsupported value"],
            )
        ],
        service_candidates=[
            ServiceCandidate(
                service_id="invented_service",
                match_level="strong",
                reason="The provider invented this service.",
                evidence=["invented service"],
            )
        ],
        complexity_factors=[
            ComplexityFactorCandidate(
                factor_id="invented_factor",
                reason="The provider invented this factor.",
                evidence=["invented factor"],
            )
        ],
        draft_questions=[
            DraftClarifyingQuestion(
                field_id="invented_question_field",
                question="What unsupported information is needed?",
            )
        ],
    )

    result = validate_extraction_references(extraction, make_business_config())

    assert result.extraction.intake_field_findings == []
    assert result.extraction.service_candidates == []
    assert result.extraction.complexity_factors == []
    assert result.extraction.draft_questions == []
    assert len(result.validation_issues) == 4
    assert {issue.code for issue in result.validation_issues} == {
        ValidationIssueCode.UNSUPPORTED_REFERENCE
    }
    assert {issue.item_reference for issue in result.validation_issues} == {
        "invented_field",
        "invented_service",
        "invented_factor",
        "invented_question_field",
    }


def test_keeps_valid_candidates_while_rejecting_unknown_references() -> None:
    valid = ServiceCandidate(
        service_id="workflow_automation",
        match_level="possible",
        reason="The request may fit workflow automation.",
        evidence=["workflow automation"],
    )
    invalid = ServiceCandidate(
        service_id="imaginary_service",
        match_level="weak",
        reason="The provider invented this service.",
        evidence=["imaginary service"],
    )
    extraction = make_extraction(service_candidates=[valid, invalid])

    result = validate_extraction_references(extraction, make_business_config())

    assert result.extraction.service_candidates == [valid]
    assert len(result.validation_issues) == 1
    assert result.validation_issues[0].item_type == "service_candidate"
    assert result.validation_issues[0].item_reference == "imaginary_service"
