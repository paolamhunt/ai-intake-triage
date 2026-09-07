"""Unit tests for provider-facing AI extraction models."""

from typing import Any

import pytest
from pydantic import ValidationError

from ai_intake_triage.domain.enums import ServiceMatchLevel
from ai_intake_triage.domain.extraction import AIExtraction


def valid_extraction() -> dict[str, Any]:
    """Return a representative valid provider response."""
    return {
        "summary": "The client wants to automate a bookkeeping workflow.",
        "primary_pain_point": "Manual document processing takes hours each week.",
        "stated_requirements": [
            {
                "statement": "Information is entered into QuickBooks.",
                "evidence": ["putting information into QuickBooks"],
            }
        ],
        "mentioned_systems": [
            {
                "name": "QuickBooks",
                "evidence": ["QuickBooks"],
            }
        ],
        "intake_field_findings": [
            {
                "field_id": "current_systems",
                "value": "Email, QuickBooks, and a spreadsheet",
                "evidence": [
                    "attachments from emails",
                    "putting information into QuickBooks",
                    "updating a spreadsheet",
                ],
            }
        ],
        "inferred_capabilities": [
            {
                "capability": "document extraction",
                "reason": "Attachment data may need to be interpreted.",
            }
        ],
        "service_candidates": [
            {
                "service_id": "workflow_automation",
                "match_level": "strong",
                "reason": "The inquiry describes repetitive manual work.",
                "evidence": ["spending hours every week"],
            }
        ],
        "complexity_factors": [
            {
                "factor_id": "multiple_external_systems",
                "reason": "Email, accounting, and spreadsheet systems are involved.",
                "evidence": [
                    "attachments from emails",
                    "QuickBooks",
                    "spreadsheet",
                ],
            }
        ],
        "ambiguities": [],
        "contradictions": [],
        "draft_questions": [
            {
                "field_id": "volume_frequency",
                "question": "How many documents do you process each month?",
            }
        ],
    }


def test_valid_extraction_is_accepted() -> None:
    """A complete structured provider response satisfies the schema."""
    extraction = AIExtraction.model_validate(valid_extraction())

    assert extraction.summary.startswith("The client wants")
    assert extraction.service_candidates[0].match_level is (ServiceMatchLevel.STRONG)
    assert extraction.intake_field_findings[0].field_id == "current_systems"


def test_final_decisions_are_rejected_from_ai_output() -> None:
    """The provider cannot submit authoritative routing or complexity fields."""
    extraction_data = valid_extraction()
    extraction_data["recommended_action"] = "proceed_to_discovery"
    extraction_data["complexity"] = "low"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        AIExtraction.model_validate(extraction_data)


def test_invalid_stable_identifier_is_rejected() -> None:
    """Provider-supplied IDs must follow the domain identifier format."""
    extraction_data = valid_extraction()
    extraction_data["service_candidates"][0]["service_id"] = "Workflow Automation"

    with pytest.raises(ValidationError):
        AIExtraction.model_validate(extraction_data)


def test_short_evidence_excerpt_is_rejected() -> None:
    """Evidence must contain enough content to be meaningfully reviewed."""
    extraction_data = valid_extraction()
    extraction_data["mentioned_systems"][0]["evidence"] = ["API"]

    with pytest.raises(ValidationError):
        AIExtraction.model_validate(extraction_data)


def test_contradiction_requires_multiple_excerpts() -> None:
    """A claimed contradiction must identify at least two conflicting excerpts."""
    extraction_data = valid_extraction()
    extraction_data["contradictions"] = [
        {
            "description": "The requested timing conflicts.",
            "evidence": ["needed tomorrow"],
        }
    ]

    with pytest.raises(ValidationError):
        AIExtraction.model_validate(extraction_data)


def test_extraction_collection_limits_are_enforced() -> None:
    """Provider output cannot create unbounded result collections."""
    extraction_data = valid_extraction()
    extraction_data["stated_requirements"] = [
        {
            "statement": f"Requirement {number}",
            "evidence": ["valid evidence"],
        }
        for number in range(26)
    ]

    with pytest.raises(ValidationError):
        AIExtraction.model_validate(extraction_data)
