"""End-to-end domain tests for building a trusted triage result."""

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import (
    ComplexityLevel,
    RecommendedAction,
    ValidationIssueCode,
)
from ai_intake_triage.domain.extraction import (
    AIExtraction,
    ComplexityFactorCandidate,
    IntakeFieldFinding,
    ServiceCandidate,
)
from ai_intake_triage.domain.triage_builder import build_triage_result


def make_business_config() -> BusinessConfig:
    """Build a compact configuration spanning the assembled rules."""
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
                    "description": "Automation of repetitive workflows.",
                    "typical_capabilities": ["Process automation"],
                    "required_information": ["project_goal"],
                    "base_complexity_points": 2,
                },
                {
                    "id": "api_integration",
                    "name": "API Integration",
                    "description": "Integration between software systems.",
                    "typical_capabilities": ["System integration"],
                    "required_information": ["project_goal"],
                    "base_complexity_points": 3,
                },
            ],
            "complexity": {
                "factors": [
                    {
                        "id": "external_integration",
                        "description": "Requires an external integration.",
                        "points": 3,
                    }
                ],
                "thresholds": {"low_max": 3, "medium_max": 8},
            },
            "routing": {"discovery_match_levels": ["strong", "possible"]},
        }
    )


def test_builds_complete_trusted_triage_result() -> None:
    inquiry_text = "We need to automate this workflow and connect email."
    project_goal = IntakeFieldFinding(
        field_id="project_goal",
        value="Automate the workflow",
        evidence=["automate this workflow"],
    )
    complexity_factor = ComplexityFactorCandidate(
        factor_id="external_integration",
        reason="The workflow must connect to email.",
        evidence=["connect email"],
    )
    possible = ServiceCandidate(
        service_id="api_integration",
        match_level="possible",
        reason="The request involves connecting email.",
        evidence=["connect email"],
    )
    strong = ServiceCandidate(
        service_id="workflow_automation",
        match_level="strong",
        reason="The request explicitly asks for workflow automation.",
        evidence=["automate this workflow"],
    )
    extraction = AIExtraction(
        summary="The client wants to automate an email-related workflow.",
        primary_pain_point="Manual workflow",
        intake_field_findings=[project_goal],
        service_candidates=[possible, strong],
        complexity_factors=[complexity_factor],
    )

    result = build_triage_result(
        extraction,
        inquiry_text=inquiry_text,
        business_config=make_business_config(),
    )

    assert result.service_candidates == [strong, possible]
    assert result.missing_information == []
    assert result.complexity.level is ComplexityLevel.MEDIUM
    assert result.complexity.score == 5
    assert result.recommended_action.action is RecommendedAction.PROCEED_TO_DISCOVERY
    assert result.human_review.required is True
    assert len(result.human_review.reasons) == 1
    assert result.validation_issues == []


def test_incomplete_inquiry_requests_only_required_information() -> None:
    inquiry_text = "Please automate this workflow."
    extraction = AIExtraction(
        summary="The client wants workflow automation.",
        primary_pain_point="Manual workflow",
        service_candidates=[
            ServiceCandidate(
                service_id="workflow_automation",
                match_level="strong",
                reason="The request explicitly asks for automation.",
                evidence=["automate this workflow"],
            )
        ],
    )

    result = build_triage_result(
        extraction,
        inquiry_text=inquiry_text,
        business_config=make_business_config(),
    )

    assert [item.field_id for item in result.missing_information] == ["project_goal"]
    assert (
        result.recommended_action.action is RecommendedAction.REQUEST_MORE_INFORMATION
    )
    assert any(
        "Required information is missing" in reason
        for reason in result.human_review.reasons
    )


def test_rejected_only_service_match_produces_safe_mismatch_result() -> None:
    extraction = AIExtraction(
        summary="The client wants assistance.",
        primary_pain_point="Unknown",
        service_candidates=[
            ServiceCandidate(
                service_id="workflow_automation",
                match_level="strong",
                reason="The provider inferred workflow automation.",
                evidence=["words the client never supplied"],
            )
        ],
    )

    result = build_triage_result(
        extraction,
        inquiry_text="I need some help with my business.",
        business_config=make_business_config(),
    )

    assert result.service_candidates == []
    assert result.complexity.level is ComplexityLevel.UNKNOWN
    assert result.complexity.score is None
    assert result.recommended_action.action is RecommendedAction.REVIEW_SERVICE_MISMATCH
    assert [issue.code for issue in result.validation_issues] == [
        ValidationIssueCode.UNTRACEABLE_EVIDENCE
    ]
    assert len(result.human_review.reasons) == 3
