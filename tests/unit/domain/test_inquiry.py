"""Unit tests for incoming inquiry validation."""

import pytest
from pydantic import ValidationError

from ai_intake_triage.domain.inquiry import (
    CustomerContact,
    InquirySource,
    InquirySubmission,
)

VALID_INQUIRY = "Please help automate our weekly bookkeeping workflow."


def test_submission_accepts_email_reply_path() -> None:
    """A valid customer email satisfies the reply-path requirement."""
    submission = InquirySubmission(
        inquiry_text=f"  {VALID_INQUIRY}  ",
        customer=CustomerContact(
            name="  Jane Smith  ",
            email="jane@example.com",
        ),
        source=InquirySource(channel="  website  "),
    )

    assert submission.inquiry_text == VALID_INQUIRY
    assert submission.customer.name == "Jane Smith"
    assert str(submission.customer.email) == "jane@example.com"
    assert submission.source.channel == "website"


def test_submission_accepts_source_reference_reply_path() -> None:
    """A platform reference is sufficient when direct contact is unavailable."""
    submission = InquirySubmission(
        inquiry_text=VALID_INQUIRY,
        customer=CustomerContact(name="Jane Smith"),
        source=InquirySource(
            channel="upwork",
            external_reference="proposal-12345",
        ),
    )

    assert submission.source.external_reference == "proposal-12345"


def test_submission_accepts_phone_reply_path() -> None:
    """A reasonably formatted phone number satisfies the reply path."""
    submission = InquirySubmission(
        inquiry_text=VALID_INQUIRY,
        customer=CustomerContact(phone="+1 (402) 555-0100"),
        source=InquirySource(channel="referral"),
    )

    assert submission.customer.phone == "+1 (402) 555-0100"


def test_submission_rejects_missing_reply_path() -> None:
    """An inquiry must provide some way for the operator to follow up."""
    with pytest.raises(ValidationError, match="At least one reply path"):
        InquirySubmission(
            inquiry_text=VALID_INQUIRY,
            customer=CustomerContact(),
            source=InquirySource(channel="website"),
        )


def test_submission_rejects_invalid_email() -> None:
    """Malformed email addresses do not qualify as a reply path."""
    with pytest.raises(ValidationError):
        CustomerContact(email="not-an-email")


def test_submission_rejects_invalid_phone_characters() -> None:
    """Phone fields reject unexpected alphabetic content."""
    with pytest.raises(ValidationError):
        CustomerContact(phone="call-me-maybe")


def test_submission_rejects_unknown_fields() -> None:
    """Unexpected input is rejected instead of silently discarded."""
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        InquirySubmission.model_validate(
            {
                "inquiry_text": VALID_INQUIRY,
                "customer": {"email": "jane@example.com"},
                "source": {"channel": "website"},
                "unexpected": "value",
            }
        )


def test_submission_rejects_too_short_inquiry() -> None:
    """Meaningless short text is rejected before AI processing."""
    with pytest.raises(ValidationError):
        InquirySubmission(
            inquiry_text="help",
            customer=CustomerContact(email="jane@example.com"),
            source=InquirySource(channel="website"),
        )
