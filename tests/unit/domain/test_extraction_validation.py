"""Tests for deterministic validation of AI extraction evidence."""

from ai_intake_triage.domain.enums import ValidationIssueCode
from ai_intake_triage.domain.extraction import (
    AIExtraction,
    EvidenceBackedStatement,
    MentionedSystem,
)
from ai_intake_triage.domain.extraction_validation import validate_extraction_evidence


def test_keeps_item_when_all_evidence_is_traceable() -> None:
    inquiry_text = "We download invoice attachments from email every Friday."
    extraction = AIExtraction(
        summary="The client wants to automate invoice handling.",
        primary_pain_point="Manual invoice processing",
        stated_requirements=[
            EvidenceBackedStatement(
                statement="Downloads invoice attachments",
                evidence=["download invoice attachments", "every Friday"],
            )
        ],
    )

    result = validate_extraction_evidence(extraction, inquiry_text)

    assert result.extraction.stated_requirements == extraction.stated_requirements
    assert result.validation_issues == []


def test_rejects_whole_item_when_any_evidence_is_untraceable() -> None:
    inquiry_text = "We download invoice attachments from email every Friday."
    extraction = AIExtraction(
        summary="The client wants to automate invoice handling.",
        primary_pain_point="Manual invoice processing",
        stated_requirements=[
            EvidenceBackedStatement(
                statement="Downloads and renames invoice attachments",
                evidence=["download invoice attachments", "renames the files"],
            )
        ],
    )

    result = validate_extraction_evidence(extraction, inquiry_text)

    assert result.extraction.stated_requirements == []
    assert len(result.validation_issues) == 1
    issue = result.validation_issues[0]
    assert issue.code is ValidationIssueCode.UNTRACEABLE_EVIDENCE
    assert issue.item_type == "stated_requirement"
    assert issue.item_reference == "Downloads and renames invoice attachments"
    assert "renames the files" in issue.message


def test_preserves_valid_items_while_rejecting_invalid_items() -> None:
    inquiry_text = "We download invoice attachments from email."
    valid_system = MentionedSystem(name="Email", evidence=["email"])
    invalid_system = MentionedSystem(name="QuickBooks", evidence=["QuickBooks"])
    extraction = AIExtraction(
        summary="The client wants to automate invoice handling.",
        primary_pain_point="Manual invoice processing",
        mentioned_systems=[valid_system, invalid_system],
    )

    result = validate_extraction_evidence(extraction, inquiry_text)

    assert result.extraction.mentioned_systems == [valid_system]
    assert len(result.validation_issues) == 1
    assert result.validation_issues[0].item_type == "mentioned_system"
    assert result.validation_issues[0].item_reference == "QuickBooks"


def test_uses_existing_normalized_evidence_matching() -> None:
    inquiry_text = "EMAIL\n   Attachments arrive weekly."
    extraction = AIExtraction(
        summary="The client receives email attachments.",
        primary_pain_point="Manual attachment handling",
        mentioned_systems=[
            MentionedSystem(
                name="Email",
                evidence=["email attachments"],
            )
        ],
    )

    result = validate_extraction_evidence(extraction, inquiry_text)

    assert result.extraction.mentioned_systems == extraction.mentioned_systems
    assert result.validation_issues == []
