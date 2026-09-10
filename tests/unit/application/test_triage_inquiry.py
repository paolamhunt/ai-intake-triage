"""Tests for the inquiry triage application use case."""

import asyncio
import socket
from dataclasses import fields

import pytest

from ai_intake_triage.application.triage_inquiry import TriageInquiry
from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.extraction import AIExtraction, ServiceCandidate
from ai_intake_triage.domain.inquiry import (
    CustomerContact,
    InquirySource,
    InquirySubmission,
)
from ai_intake_triage.domain.triage import TriageResult
from ai_intake_triage.providers.base import ExtractionUnavailableError
from ai_intake_triage.providers.fake import ExtractionRequest, StaticExtractionProvider

INQUIRY_TEXT = "Please help automate our weekly bookkeeping workflow."


def make_business_config() -> BusinessConfig:
    """Build a compact valid business configuration."""
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
                    "base_complexity_points": 2,
                }
            ],
            "complexity": {
                "factors": [
                    {
                        "id": "integration",
                        "description": "Requires an integration.",
                        "points": 1,
                    }
                ],
                "thresholds": {"low_max": 3, "medium_max": 6},
            },
            "routing": {"discovery_match_levels": ["strong"]},
        }
    )


def make_inquiry() -> InquirySubmission:
    """Build a valid inquiry containing private boundary-excluded fields."""
    return InquirySubmission(
        inquiry_text=INQUIRY_TEXT,
        customer=CustomerContact(
            name="Jane Smith",
            email="jane@example.com",
            phone="+1 402 555 0100",
        ),
        source=InquirySource(
            channel="website",
            external_reference="lead-123",
        ),
    )


def make_extraction() -> AIExtraction:
    """Build provider output with evidence from the inquiry text."""
    return AIExtraction(
        summary="The client wants bookkeeping workflow automation.",
        primary_pain_point="A manual weekly bookkeeping workflow.",
        service_candidates=[
            ServiceCandidate(
                service_id="workflow_automation",
                match_level="strong",
                reason="The inquiry requests workflow automation.",
                evidence=["automate our weekly bookkeeping workflow"],
            )
        ],
    )


def test_valid_inquiry_flows_through_provider_to_trusted_result() -> None:
    provider = StaticExtractionProvider(make_extraction())
    use_case = TriageInquiry(provider, make_business_config())

    result = asyncio.run(use_case.execute(make_inquiry()))

    assert isinstance(result, TriageResult)
    assert result.summary == "The client wants bookkeeping workflow automation."
    assert [candidate.service_id for candidate in result.service_candidates] == [
        "workflow_automation"
    ]


def test_provider_is_called_once_with_only_boundary_inputs() -> None:
    inquiry = make_inquiry()
    business_config = make_business_config()
    provider = StaticExtractionProvider(make_extraction())
    use_case = TriageInquiry(provider, business_config)

    asyncio.run(use_case.execute(inquiry))

    assert len(provider.calls) == 1
    assert provider.calls[0].inquiry_text == inquiry.inquiry_text
    assert provider.calls[0].business_config is business_config
    assert {field.name for field in fields(ExtractionRequest)} == {
        "inquiry_text",
        "business_config",
    }
    assert not hasattr(provider.calls[0], "customer")
    assert not hasattr(provider.calls[0], "source")


def test_provider_failure_propagates_as_same_instance() -> None:
    failure = ExtractionUnavailableError("provider unavailable")

    class FailingProvider:
        async def extract(
            self,
            *,
            inquiry_text: str,
            business_config: BusinessConfig,
        ) -> AIExtraction:
            raise failure

    use_case = TriageInquiry(FailingProvider(), make_business_config())

    with pytest.raises(ExtractionUnavailableError) as caught:
        asyncio.run(use_case.execute(make_inquiry()))

    assert caught.value is failure


def test_execute_does_not_use_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError(f"unexpected network call: {args!r}, {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", reject_network)
    use_case = TriageInquiry(
        StaticExtractionProvider(make_extraction()),
        make_business_config(),
    )

    result = asyncio.run(use_case.execute(make_inquiry()))

    assert isinstance(result, TriageResult)
