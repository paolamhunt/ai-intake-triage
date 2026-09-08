"""Deterministic reasons for mandatory human review."""

from collections.abc import Sequence

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.extraction import AIExtraction
from ai_intake_triage.domain.service_ranking import rank_service_candidates
from ai_intake_triage.domain.triage import (
    HumanReviewRequirement,
    MissingInformation,
    ValidationIssue,
)

BASE_REVIEW_REASON = (
    "AI-assisted triage requires human approval before consequential action."
)


def build_human_review_requirement(
    extraction: AIExtraction,
    business_config: BusinessConfig,
    *,
    missing_information: Sequence[MissingInformation],
    validation_issues: Sequence[ValidationIssue],
) -> HumanReviewRequirement:
    """Describe why an operator must review a successful triage result."""
    reasons = [BASE_REVIEW_REASON]

    if validation_issues:
        count = len(validation_issues)
        noun = "item was" if count == 1 else "items were"
        reasons.append(
            f"{count} AI-generated {noun} rejected during deterministic validation."
        )

    if extraction.ambiguities or extraction.contradictions:
        reasons.append("The inquiry contains material ambiguity or contradiction.")

    ranked_candidates = rank_service_candidates(extraction.service_candidates)
    if not ranked_candidates:
        reasons.append("No validated service match remains for this inquiry.")
    elif (
        ranked_candidates[0].match_level
        not in business_config.routing.discovery_match_levels
    ):
        reasons.append("The best service match is not discovery-eligible.")

    if missing_information:
        reasons.append("Required information is missing for the best service match.")

    return HumanReviewRequirement(required=True, reasons=reasons)
