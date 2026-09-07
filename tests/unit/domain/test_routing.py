"""Tests for deterministic next-action routing."""

import pytest

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import (
    InformationPriority,
    RecommendedAction,
)
from ai_intake_triage.domain.extraction import (
    AIExtraction,
    Ambiguity,
    Contradiction,
    ServiceCandidate,
)
from ai_intake_triage.domain.routing import recommend_next_action
from ai_intake_triage.domain.triage import MissingInformation


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


def candidate(match_level: str) -> ServiceCandidate:
    """Build a configured service candidate."""
    return ServiceCandidate(
        service_id="workflow_automation",
        match_level=match_level,
        reason="The inquiry describes a repetitive workflow.",
        evidence=["repetitive workflow"],
    )


def missing_project_goal() -> MissingInformation:
    """Build one required missing-information item."""
    return MissingInformation(
        field_id="project_goal",
        priority=InformationPriority.REQUIRED,
        reason="Required to assess workflow automation.",
        question="What outcome are you hoping to achieve?",
    )


@pytest.mark.parametrize("uncertainty_kind", ["ambiguity", "contradiction"])
def test_material_uncertainty_routes_to_manual_assessment_first(
    uncertainty_kind: str,
) -> None:
    updates: dict[str, object]
    if uncertainty_kind == "ambiguity":
        updates = {
            "ambiguities": [
                Ambiguity(
                    description="The requested outcome is unclear.",
                    evidence=["make it better"],
                )
            ]
        }
    else:
        updates = {
            "contradictions": [
                Contradiction(
                    description="The requested timing conflicts.",
                    evidence=["needed tomorrow", "no deadline"],
                )
            ]
        }

    result = recommend_next_action(
        extraction(**updates),
        make_business_config(),
        missing_information=[],
    )

    assert result.action is RecommendedAction.MANUAL_ASSESSMENT


def test_no_candidate_routes_to_service_mismatch_review() -> None:
    result = recommend_next_action(
        extraction(),
        make_business_config(),
        missing_information=[],
    )

    assert result.action is RecommendedAction.REVIEW_SERVICE_MISMATCH


def test_ineligible_best_match_routes_to_manual_assessment() -> None:
    result = recommend_next_action(
        extraction(service_candidates=[candidate("weak")]),
        make_business_config(),
        missing_information=[missing_project_goal()],
    )

    assert result.action is RecommendedAction.MANUAL_ASSESSMENT


def test_missing_required_information_routes_to_information_request() -> None:
    result = recommend_next_action(
        extraction(service_candidates=[candidate("strong")]),
        make_business_config(),
        missing_information=[missing_project_goal()],
    )

    assert result.action is RecommendedAction.REQUEST_MORE_INFORMATION


def test_eligible_complete_inquiry_routes_to_discovery() -> None:
    result = recommend_next_action(
        extraction(service_candidates=[candidate("possible")]),
        make_business_config(),
        missing_information=[],
    )

    assert result.action is RecommendedAction.PROCEED_TO_DISCOVERY
