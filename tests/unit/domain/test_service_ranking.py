"""Tests for deterministic ranking of validated service candidates."""

from ai_intake_triage.domain.extraction import ServiceCandidate
from ai_intake_triage.domain.service_ranking import rank_service_candidates


def make_candidate(
    service_id: str,
    match_level: str,
) -> ServiceCandidate:
    """Build a concise service candidate for ranking tests."""
    return ServiceCandidate(
        service_id=service_id,
        match_level=match_level,
        reason=f"The inquiry may match {service_id}.",
        evidence=["client request"],
    )


def test_ranks_candidates_by_constrained_match_strength() -> None:
    weak = make_candidate("weak_service", "weak")
    strong = make_candidate("strong_service", "strong")
    possible = make_candidate("possible_service", "possible")

    ranked = rank_service_candidates([weak, strong, possible])

    assert ranked == [strong, possible, weak]


def test_preserves_provider_order_within_same_match_level() -> None:
    first_possible = make_candidate("first_possible", "possible")
    second_possible = make_candidate("second_possible", "possible")
    strong = make_candidate("strong_service", "strong")

    ranked = rank_service_candidates([first_possible, second_possible, strong])

    assert ranked == [strong, first_possible, second_possible]


def test_returns_empty_list_when_no_candidates_remain() -> None:
    assert rank_service_candidates([]) == []


def test_does_not_mutate_original_candidate_list() -> None:
    weak = make_candidate("weak_service", "weak")
    strong = make_candidate("strong_service", "strong")
    original = [weak, strong]

    ranked = rank_service_candidates(original)

    assert original == [weak, strong]
    assert ranked == [strong, weak]
