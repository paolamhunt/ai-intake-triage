"""Application use case for triaging one inquiry."""

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.inquiry import InquirySubmission
from ai_intake_triage.domain.triage import TriageResult
from ai_intake_triage.domain.triage_builder import build_triage_result
from ai_intake_triage.providers.base import ExtractionProvider


class TriageInquiry:
    """Coordinate provider extraction and deterministic triage."""

    def __init__(
        self,
        provider: ExtractionProvider,
        business_config: BusinessConfig,
    ) -> None:
        self._provider = provider
        self._business_config = business_config

    async def execute(self, inquiry: InquirySubmission) -> TriageResult:
        """Produce a trusted triage result for a validated inquiry."""
        extraction = await self._provider.extract(
            inquiry_text=inquiry.inquiry_text,
            business_config=self._business_config,
        )
        return build_triage_result(
            extraction,
            inquiry_text=inquiry.inquiry_text,
            business_config=self._business_config,
        )
