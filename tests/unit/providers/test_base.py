"""Tests for provider-neutral extraction failures."""

import pytest

from ai_intake_triage.providers.base import (
    ExtractionProviderError,
    ExtractionResponseError,
    ExtractionTimeoutError,
    ExtractionUnavailableError,
)


@pytest.mark.parametrize(
    "error_type",
    [
        ExtractionTimeoutError,
        ExtractionUnavailableError,
        ExtractionResponseError,
    ],
)
def test_specific_failures_share_provider_neutral_base(
    error_type: type[ExtractionProviderError],
) -> None:
    assert issubclass(error_type, ExtractionProviderError)
