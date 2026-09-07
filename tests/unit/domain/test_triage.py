"""Unit tests for trusted triage-result models."""

from typing import Any

import pytest
from pydantic import ValidationError

from ai_intake_triage.domain.enums import (
    ComplexityLevel,
    RecommendedAction,
)
from ai_intake_triage.domain.triage import TriageResult


def valid_triage_result() -> dict[str, Any]:
    """Return a minimal valid trusted triage result."""
    return {
        "summary": "The client wants help understanding an automation project.",
        "primary_pain_point": "The current workflow requires manual effort.",
        "stated_requirements": [],
        "mentioned_systems": [],
        "intake_field_findings": [],
        "inferred_capabilities": [],
        "service_candidates": [],
        "missing_information": [],
        "complexity": {
            "level": "unknown",
            "score": None,
            "factors": [],
            "unknowns": [],
        },
        "ambiguities": [],
        "contradictions": [],
        "recommended_action": {
            "action": "manual_assessment",
            "reason": "No usable service candidate is available.",
        },
        "human_review": {
            "required": True,
            "reasons": ["Every V1 triage result requires human review."],
        },
        "validation_issues": [],
    }


def test_valid_triage_result_is_accepted() -> None:
    """A complete trusted result satisfies the final schema."""
    result = TriageResult.model_validate(valid_triage_result())

    assert result.complexity.level is ComplexityLevel.UNKNOWN
    assert result.recommended_action.action is RecommendedAction.MANUAL_ASSESSMENT
    assert result.human_review.required is True


def test_unknown_complexity_rejects_numeric_score() -> None:
    """Unknown complexity cannot imply a meaningful numeric score."""
    result_data = valid_triage_result()
    result_data["complexity"]["score"] = 2

    with pytest.raises(ValidationError, match="cannot have a score"):
        TriageResult.model_validate(result_data)


def test_known_complexity_requires_numeric_score() -> None:
    """Assigned complexity must preserve the score that produced it."""
    result_data = valid_triage_result()
    result_data["complexity"]["level"] = "medium"

    with pytest.raises(ValidationError, match="must have a score"):
        TriageResult.model_validate(result_data)


def test_human_review_cannot_be_disabled() -> None:
    """Every V1 result must remain subject to human review."""
    result_data = valid_triage_result()
    result_data["human_review"]["required"] = False

    with pytest.raises(ValidationError):
        TriageResult.model_validate(result_data)


def test_arbitrary_recommended_action_is_rejected() -> None:
    """Only deterministic workflow actions belong in a trusted result."""
    result_data = valid_triage_result()
    result_data["recommended_action"]["action"] = "email_the_customer"

    with pytest.raises(ValidationError):
        TriageResult.model_validate(result_data)
