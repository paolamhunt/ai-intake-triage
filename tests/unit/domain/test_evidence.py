"""Unit tests for deterministic evidence traceability."""

import pytest

from ai_intake_triage.domain.evidence import evidence_is_traceable


@pytest.mark.parametrize(
    ("inquiry", "evidence"),
    [
        (
            "I update QuickBooks every Friday.",
            "update QuickBooks every Friday",
        ),
        (
            "I update QUICKBOOKS   every Friday.",
            "update quickbooks every Friday",
        ),
        (
            "I use ＱｕｉｃｋＢｏｏｋｓ for invoices.",
            "QuickBooks",
        ),
        (
            "Attachments arrive by email.\nI rename each file.",
            "email. I rename",
        ),
    ],
)
def test_traceable_evidence_is_accepted(
    inquiry: str,
    evidence: str,
) -> None:
    """Harmless case, Unicode, and whitespace differences are accepted."""
    assert evidence_is_traceable(inquiry, evidence) is True


@pytest.mark.parametrize(
    "evidence",
    [
        "QuickBooks Online Advanced",
        "The client processes invoices automatically.",
        "",
        "   ",
    ],
)
def test_untraceable_evidence_is_rejected(evidence: str) -> None:
    """Invented, paraphrased, and empty evidence cannot count as stated."""
    inquiry = "I manually enter information into QuickBooks."

    assert evidence_is_traceable(inquiry, evidence) is False
