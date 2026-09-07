"""Tests for deterministic missing-information detection."""

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import InformationPriority
from ai_intake_triage.domain.extraction import (
    AIExtraction,
    DraftClarifyingQuestion,
    IntakeFieldFinding,
    ServiceCandidate,
)
from ai_intake_triage.domain.missing_information import detect_missing_information


def make_business_config() -> BusinessConfig:
    """Build a configuration with distinct service requirements."""
    fields = [
        ("project_goal", "What outcome are you hoping to achieve?"),
        ("monthly_volume", "How many items are processed each month?"),
        ("current_tools", "Which tools are currently involved?"),
    ]
    return BusinessConfig.model_validate(
        {
            "version": "1.0.0",
            "business": {
                "name": "Example Consulting",
                "description": "An example service business.",
            },
            "intake_fields": [
                {
                    "id": field_id,
                    "description": f"Information about {field_id}.",
                    "default_question": question,
                }
                for field_id, question in fields
            ],
            "services": [
                {
                    "id": "workflow_automation",
                    "name": "Workflow Automation",
                    "description": "Automation of repetitive workflows.",
                    "typical_capabilities": ["Process automation"],
                    "required_information": ["project_goal", "monthly_volume"],
                    "optional_information": ["current_tools"],
                    "base_complexity_points": 1,
                },
                {
                    "id": "api_integration",
                    "name": "API Integration",
                    "description": "Integration between software systems.",
                    "typical_capabilities": ["System integration"],
                    "required_information": ["current_tools"],
                    "base_complexity_points": 2,
                },
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


def candidate(service_id: str, match_level: str) -> ServiceCandidate:
    """Build a service candidate."""
    return ServiceCandidate(
        service_id=service_id,
        match_level=match_level,
        reason=f"The inquiry may match {service_id}.",
        evidence=["client request"],
    )


def extraction(**updates: object) -> AIExtraction:
    """Build an extraction with required provider fields."""
    return AIExtraction(
        summary="The client wants assistance.",
        primary_pain_point="Manual work",
        **updates,
    )


def test_reports_only_missing_required_fields_for_best_candidate() -> None:
    result = detect_missing_information(
        extraction(
            service_candidates=[
                candidate("api_integration", "possible"),
                candidate("workflow_automation", "strong"),
            ]
        ),
        make_business_config(),
    )

    assert [item.field_id for item in result] == [
        "project_goal",
        "monthly_volume",
    ]
    assert all(item.priority is InformationPriority.REQUIRED for item in result)
    assert "current_tools" not in {item.field_id for item in result}


def test_present_validated_finding_is_not_missing() -> None:
    result = detect_missing_information(
        extraction(
            service_candidates=[candidate("workflow_automation", "strong")],
            intake_field_findings=[
                IntakeFieldFinding(
                    field_id="project_goal",
                    value="Reduce time spent processing invoices",
                    evidence=["processing invoices"],
                )
            ],
        ),
        make_business_config(),
    )

    assert [item.field_id for item in result] == ["monthly_volume"]


def test_prefers_validated_ai_question_over_default_question() -> None:
    result = detect_missing_information(
        extraction(
            service_candidates=[candidate("workflow_automation", "strong")],
            draft_questions=[
                DraftClarifyingQuestion(
                    field_id="monthly_volume",
                    question="Approximately how many invoices arrive each month?",
                )
            ],
        ),
        make_business_config(),
    )

    questions = {item.field_id: item.question for item in result}
    assert questions["monthly_volume"] == (
        "Approximately how many invoices arrive each month?"
    )
    assert questions["project_goal"] == "What outcome are you hoping to achieve?"


def test_returns_no_service_specific_missing_information_without_candidate() -> None:
    result = detect_missing_information(extraction(), make_business_config())

    assert result == []


def test_still_reports_required_information_for_weak_best_match() -> None:
    result = detect_missing_information(
        extraction(
            service_candidates=[candidate("api_integration", "weak")],
        ),
        make_business_config(),
    )

    assert [item.field_id for item in result] == ["current_tools"]
