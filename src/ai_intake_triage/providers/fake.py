"""Deterministic extraction provider for tests and local use."""

from dataclasses import dataclass

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.extraction import AIExtraction


@dataclass(frozen=True, slots=True)
class ExtractionRequest:
    """Inputs received across the extraction provider boundary."""

    inquiry_text: str
    business_config: BusinessConfig


class StaticExtractionProvider:
    """Return one configured extraction and record every request."""

    def __init__(self, extraction: AIExtraction) -> None:
        self._extraction = extraction
        self._calls: list[ExtractionRequest] = []

    @property
    def calls(self) -> tuple[ExtractionRequest, ...]:
        """Return the recorded requests in call order."""
        return tuple(self._calls)

    async def extract(
        self,
        *,
        inquiry_text: str,
        business_config: BusinessConfig,
    ) -> AIExtraction:
        """Record the request and return the configured extraction."""
        self._calls.append(
            ExtractionRequest(
                inquiry_text=inquiry_text,
                business_config=business_config,
            )
        )
        return self._extraction
