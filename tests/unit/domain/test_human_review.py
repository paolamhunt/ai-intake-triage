"""Tests for deterministic human-review requirements."""

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import (
    InformationPriority,
    ValidationIssueCode,
)
from ai_intake_triage.domain.extraction import AIExtraction, Ambiguity, ServiceCandidate
from ai_intake_triage.domain.human_review import build_human_review_requirement
from ai_intake_triage.domain.triage import MissingInformation, ValidationIssue

BASE_REASON = "AI-assisted triage requires human approval before consequential action."


def make_business_config() -> BusinessConfig:
    """Build a minimal configuration with explicit discovery eligibility."""
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
                    "base_complexity_points": 1,
                }
            ],
            "complexity": {
                "factors": [
                    {
                        "id": "external_integration",
                        "description": "Requires an external integration.",
                        "points": 2,
                    }
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


def candidate(match_level: str = "strong") -> ServiceCandidate:
    """Build a configured service candidate."""
    return ServiceCandidate(
        service_id="workflow_automation",
        match_level=match_level,
        reason="The inquiry describes a repetitive workflow.",
        evidence=["repetitive workflow"],
    )


def test_always_requires_human_approval() -> None:
    result = build_human_review_requirement(
        extraction(service_candidates=[candidate()]),
        make_business_config(),
        missing_information=[],
        validation_issues=[],
    )

    assert result.required is True
    assert result.reasons == [BASE_REASON]


def test_summarizes_rejected_items_as_one_review_reason() -> None:
    issues = [
        ValidationIssue(
            code=ValidationIssueCode.UNTRACEABLE_EVIDENCE,
            item_type="mentioned_system",
            item_reference="Invented System",
            message="The evidence was not found.",
        ),
        ValidationIssue(
            code=ValidationIssueCode.UNSUPPORTED_REFERENCE,
            item_type="service_candidate",
            item_reference="invented_service",
            message="The service is not configured.",
        ),
    ]

    result = build_human_review_requirement(
        extraction(service_candidates=[candidate()]),
        make_business_config(),
        missing_information=[],
        validation_issues=issues,
    )

    assert len(result.reasons) == 2
    assert result.reasons[0] == BASE_REASON
    assert "2 AI-generated items were rejected" in result.reasons[1]


def test_adds_one_reason_for_material_uncertainty() -> None:
    result = build_human_review_requirement(
        extraction(
            service_candidates=[candidate()],
            ambiguities=[
                Ambiguity(
                    description="The requested outcome is unclear.",
                    evidence=["make it better"],
                )
            ],
        ),
        make_business_config(),
        missing_information=[],
        validation_issues=[],
    )

    assert len(result.reasons) == 2
    assert "ambiguity or contradiction" in result.reasons[1]


def test_adds_reason_when_no_service_candidate_remains() -> None:
    result = build_human_review_requirement(
        extraction(),
        make_business_config(),
        missing_information=[],
        validation_issues=[],
    )

    assert any("No validated service match" in reason for reason in result.reasons)


def test_adds_reason_when_best_match_is_not_discovery_eligible() -> None:
    result = build_human_review_requirement(
        extraction(service_candidates=[candidate("weak")]),
        make_business_config(),
        missing_information=[],
        validation_issues=[],
    )

    assert any("not discovery-eligible" in reason for reason in result.reasons)


def test_adds_one_reason_for_missing_required_information() -> None:
    missing = [
        MissingInformation(
            field_id="project_goal",
            priority=InformationPriority.REQUIRED,
            reason="Required to assess workflow automation.",
            question="What outcome are you hoping to achieve?",
        )
    ]

    result = build_human_review_requirement(
        extraction(service_candidates=[candidate()]),
        make_business_config(),
        missing_information=missing,
        validation_issues=[],
    )

    assert any("Required information is missing" in reason for reason in result.reasons)
