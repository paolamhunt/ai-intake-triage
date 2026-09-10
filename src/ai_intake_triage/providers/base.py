"""Provider-neutral boundary for AI extraction."""

from typing import Protocol, runtime_checkable

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.extraction import AIExtraction


@runtime_checkable
class ExtractionProvider(Protocol):
    """Produce structured candidates from inquiry text."""

    async def extract(
        self,
        *,
        inquiry_text: str,
        business_config: BusinessConfig,
    ) -> AIExtraction:
        """Extract candidates using the validated business configuration."""
        ...


class ExtractionProviderError(Exception):
    """Base error for failures at the extraction provider boundary."""


class ExtractionTimeoutError(ExtractionProviderError):
    """The extraction provider did not respond before its deadline."""


class ExtractionUnavailableError(ExtractionProviderError):
    """The extraction provider is unavailable."""


class ExtractionResponseError(ExtractionProviderError):
    """The extraction provider returned an unusable response."""
