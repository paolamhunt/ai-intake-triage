"""Tests for the deterministic extraction provider fake."""

import asyncio
import inspect
import socket
from dataclasses import FrozenInstanceError, fields

import pytest

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.extraction import AIExtraction
from ai_intake_triage.providers.base import ExtractionProvider
from ai_intake_triage.providers.fake import ExtractionRequest, StaticExtractionProvider


def make_business_config() -> BusinessConfig:
    """Build the smallest valid business configuration."""
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
                    "id": "consulting",
                    "name": "Consulting",
                    "description": "General consulting services.",
                    "typical_capabilities": ["Advisory"],
                    "required_information": ["project_goal"],
                    "base_complexity_points": 1,
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
                "thresholds": {"low_max": 2, "medium_max": 5},
            },
            "routing": {"discovery_match_levels": ["strong"]},
        }
    )


def make_extraction() -> AIExtraction:
    """Build a valid static extraction."""
    return AIExtraction(
        summary="The client needs consulting support.",
        primary_pain_point="The path forward is unclear.",
    )


def test_static_provider_structurally_satisfies_protocol() -> None:
    provider = StaticExtractionProvider(make_extraction())

    assert isinstance(provider, ExtractionProvider)


def test_extract_is_async_and_returns_configured_extraction() -> None:
    extraction = make_extraction()
    provider = StaticExtractionProvider(extraction)

    assert inspect.iscoroutinefunction(provider.extract)
    result = asyncio.run(
        provider.extract(
            inquiry_text="We need consulting support.",
            business_config=make_business_config(),
        )
    )

    assert result is extraction


def test_extract_records_exact_provider_boundary_inputs() -> None:
    business_config = make_business_config()
    provider = StaticExtractionProvider(make_extraction())

    asyncio.run(
        provider.extract(
            inquiry_text="We need consulting support.",
            business_config=business_config,
        )
    )

    assert provider.calls == (
        ExtractionRequest(
            inquiry_text="We need consulting support.",
            business_config=business_config,
        ),
    )


def test_extract_does_not_use_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError(f"unexpected network call: {args!r}, {kwargs!r}")

    monkeypatch.setattr(socket, "create_connection", reject_network)
    provider = StaticExtractionProvider(make_extraction())

    result = asyncio.run(
        provider.extract(
            inquiry_text="We need consulting support.",
            business_config=make_business_config(),
        )
    )

    assert result == make_extraction()


def test_request_record_is_immutable_and_excludes_customer_contact() -> None:
    request_fields = {field.name for field in fields(ExtractionRequest)}
    request = ExtractionRequest(
        inquiry_text="We need consulting support.",
        business_config=make_business_config(),
    )

    assert request_fields == {"inquiry_text", "business_config"}
    with pytest.raises(FrozenInstanceError):
        request.inquiry_text = "Changed text"  # type: ignore[misc]
