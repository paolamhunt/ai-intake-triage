"""Deterministic selection of the recommended next workflow action."""

from collections.abc import Sequence

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import RecommendedAction
from ai_intake_triage.domain.extraction import AIExtraction
from ai_intake_triage.domain.service_ranking import rank_service_candidates
from ai_intake_triage.domain.triage import (
    MissingInformation,
    RecommendedNextAction,
)


def recommend_next_action(
    extraction: AIExtraction,
    business_config: BusinessConfig,
    *,
    missing_information: Sequence[MissingInformation],
) -> RecommendedNextAction:
    """Apply the ordered routing rules to a validated extraction."""
    if extraction.ambiguities or extraction.contradictions:
        return RecommendedNextAction(
            action=RecommendedAction.MANUAL_ASSESSMENT,
            reason=(
                "The inquiry contains material ambiguity or contradictory "
                "information that requires human interpretation."
            ),
        )

    ranked_candidates = rank_service_candidates(extraction.service_candidates)
    if not ranked_candidates:
        return RecommendedNextAction(
            action=RecommendedAction.REVIEW_SERVICE_MISMATCH,
            reason="No validated candidate matches a configured service.",
        )

    best_candidate = ranked_candidates[0]
    if best_candidate.match_level not in business_config.routing.discovery_match_levels:
        return RecommendedNextAction(
            action=RecommendedAction.MANUAL_ASSESSMENT,
            reason=(
                "The best service candidate is not eligible to proceed to discovery."
            ),
        )

    if missing_information:
        return RecommendedNextAction(
            action=RecommendedAction.REQUEST_MORE_INFORMATION,
            reason=("Required information is missing for the best service candidate."),
        )

    return RecommendedNextAction(
        action=RecommendedAction.PROCEED_TO_DISCOVERY,
        reason=(
            "The best service candidate is discovery-eligible and its required "
            "information is present."
        ),
    )
