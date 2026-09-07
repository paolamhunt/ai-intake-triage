"""Deterministic ranking for validated service candidates."""

from collections.abc import Sequence

from ai_intake_triage.domain.enums import ServiceMatchLevel
from ai_intake_triage.domain.extraction import ServiceCandidate

_MATCH_PRIORITY = {
    ServiceMatchLevel.STRONG: 0,
    ServiceMatchLevel.POSSIBLE: 1,
    ServiceMatchLevel.WEAK: 2,
}


def rank_service_candidates(
    candidates: Sequence[ServiceCandidate],
) -> list[ServiceCandidate]:
    """Rank candidates by match strength while preserving ties."""
    return sorted(
        candidates,
        key=lambda candidate: _MATCH_PRIORITY[candidate.match_level],
    )
