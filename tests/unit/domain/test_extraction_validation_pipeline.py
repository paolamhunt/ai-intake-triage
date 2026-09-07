"""Tests for the complete deterministic extraction-validation pipeline."""

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import ValidationIssueCode
from ai_intake_triage.domain.extraction import (
    AIExtraction,
    DraftClarifyingQuestion,
    InferredCapability,
    MentionedSystem,
    ServiceCandidate,
)
from ai_intake_triage.domain.extraction_validation import validate_extraction


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


def test_pipeline_accumulates_issues_from_all_validation_stages() -> None:
    first_capability = InferredCapability(
        capability="Document extraction",
        reason="Documents must be interpreted.",
    )
    duplicate_capability = InferredCapability(
        capability="  document EXTRACTION ",
        reason="This repeats the earlier capability.",
    )
    extraction = AIExtraction(
        summary="The client wants to automate emailed invoices.",
        primary_pain_point="Manual invoice processing",
        mentioned_systems=[
            MentionedSystem(
                name="Invented system claim",
                evidence=["not present in inquiry"],
            )
        ],
        inferred_capabilities=[first_capability, duplicate_capability],
        draft_questions=[
            DraftClarifyingQuestion(
                field_id="invented_field",
                question="What is the invented value?",
            )
        ],
    )

    result = validate_extraction(
        extraction,
        inquiry_text="Please automate the invoices arriving by email.",
        business_config=make_business_config(),
    )

    assert result.extraction.mentioned_systems == []
    assert result.extraction.draft_questions == []
    assert result.extraction.inferred_capabilities == [first_capability]
    assert [issue.code for issue in result.validation_issues] == [
        ValidationIssueCode.UNTRACEABLE_EVIDENCE,
        ValidationIssueCode.UNSUPPORTED_REFERENCE,
        ValidationIssueCode.DUPLICATE_ITEM,
    ]


def test_pipeline_filters_invalid_item_before_duplicate_removal() -> None:
    invalid_first = ServiceCandidate(
        service_id="workflow_automation",
        match_level="weak",
        reason="This candidate cites evidence the client never supplied.",
        evidence=["evidence that is absent"],
    )
    valid_second = ServiceCandidate(
        service_id="workflow_automation",
        match_level="strong",
        reason="The inquiry explicitly requests workflow automation.",
        evidence=["automate this workflow"],
    )
    extraction = AIExtraction(
        summary="The client wants workflow automation.",
        primary_pain_point="Manual work",
        service_candidates=[invalid_first, valid_second],
    )

    result = validate_extraction(
        extraction,
        inquiry_text="Can you automate this workflow for us?",
        business_config=make_business_config(),
    )

    assert result.extraction.service_candidates == [valid_second]
    assert [issue.code for issue in result.validation_issues] == [
        ValidationIssueCode.UNTRACEABLE_EVIDENCE
    ]
