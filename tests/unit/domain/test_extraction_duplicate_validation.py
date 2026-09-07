"""Tests for deterministic duplicate removal from AI extraction output."""

from ai_intake_triage.domain.enums import ValidationIssueCode
from ai_intake_triage.domain.extraction import (
    AIExtraction,
    IntakeFieldFinding,
    MentionedSystem,
    ServiceCandidate,
)
from ai_intake_triage.domain.extraction_validation import (
    validate_extraction_duplicates,
)


def make_extraction(**updates: object) -> AIExtraction:
    """Build an extraction with required fields and selected candidates."""
    return AIExtraction(
        summary="The client wants help automating a workflow.",
        primary_pain_point="Manual processing",
        **updates,
    )


def test_removes_later_text_duplicate_after_normalization() -> None:
    first = MentionedSystem(
        name="QuickBooks Online",
        evidence=["QuickBooks Online"],
    )
    duplicate = MentionedSystem(
        name="  quickbooks   ONLINE  ",
        evidence=["QuickBooks Online"],
    )
    extraction = make_extraction(mentioned_systems=[first, duplicate])

    result = validate_extraction_duplicates(extraction)

    assert result.extraction.mentioned_systems == [first]
    assert len(result.validation_issues) == 1
    issue = result.validation_issues[0]
    assert issue.code is ValidationIssueCode.DUPLICATE_ITEM
    assert issue.item_type == "mentioned_system"
    assert issue.item_reference == "quickbooks online"


def test_removes_later_duplicate_config_by_configured_identifier() -> None:
    first = IntakeFieldFinding(
        field_id="monthly_volume",
        value="About 100 invoices",
        evidence=["100 invoices"],
    )
    duplicate = IntakeFieldFinding(
        field_id="monthly_volume",
        value="One hundred invoices each month",
        evidence=["hundred invoices"],
    )
    extraction = make_extraction(intake_field_findings=[first, duplicate])

    result = validate_extraction_duplicates(extraction)

    assert result.extraction.intake_field_findings == [first]
    assert len(result.validation_issues) == 1
    assert result.validation_issues[0].item_reference == "monthly_volume"


def test_keeps_different_service_candidates_for_the_same_request() -> None:
    workflow = ServiceCandidate(
        service_id="workflow_automation",
        match_level="strong",
        reason="The request describes repetitive manual work.",
        evidence=["repetitive manual work"],
    )
    integration = ServiceCandidate(
        service_id="api_integration",
        match_level="possible",
        reason="The same request involves connected systems.",
        evidence=["repetitive manual work"],
    )
    extraction = make_extraction(service_candidates=[workflow, integration])

    result = validate_extraction_duplicates(extraction)

    assert result.extraction.service_candidates == [workflow, integration]
    assert result.validation_issues == []


def test_preserves_first_service_candidate_and_its_ranking() -> None:
    first = ServiceCandidate(
        service_id="workflow_automation",
        match_level="strong",
        reason="The strongest interpretation appears first.",
        evidence=["strongest interpretation"],
    )
    duplicate = ServiceCandidate(
        service_id="workflow_automation",
        match_level="weak",
        reason="A conflicting duplicate appears later.",
        evidence=["duplicate appears later"],
    )
    extraction = make_extraction(service_candidates=[first, duplicate])

    result = validate_extraction_duplicates(extraction)

    assert result.extraction.service_candidates == [first]
    assert result.extraction.service_candidates[0].match_level.value == "strong"
    assert len(result.validation_issues) == 1
