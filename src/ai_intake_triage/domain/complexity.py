"""Deterministic preliminary complexity assessment."""

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import ComplexityLevel
from ai_intake_triage.domain.extraction import AIExtraction
from ai_intake_triage.domain.missing_information import detect_missing_information
from ai_intake_triage.domain.service_ranking import rank_service_candidates
from ai_intake_triage.domain.triage import ComplexityAssessment


def _level_for_score(
    score: int,
    business_config: BusinessConfig,
) -> ComplexityLevel:
    """Map a calculated score to configured complexity thresholds."""
    thresholds = business_config.complexity.thresholds
    if score <= thresholds.low_max:
        return ComplexityLevel.LOW
    if score <= thresholds.medium_max:
        return ComplexityLevel.MEDIUM
    return ComplexityLevel.HIGH


def assess_complexity(
    extraction: AIExtraction,
    business_config: BusinessConfig,
) -> ComplexityAssessment:
    """Calculate preliminary complexity from validated candidates and rules."""
    ranked_candidates = rank_service_candidates(extraction.service_candidates)
    if not ranked_candidates:
        return ComplexityAssessment(
            level=ComplexityLevel.UNKNOWN,
            score=None,
            factors=[],
            unknowns=["service_classification"],
        )

    best_candidate = ranked_candidates[0]
    service_by_id = {service.id: service for service in business_config.services}
    factor_by_id = {factor.id: factor for factor in business_config.complexity.factors}
    best_service = service_by_id[best_candidate.service_id]

    factor_points = sum(
        factor_by_id[candidate.factor_id].points
        for candidate in extraction.complexity_factors
    )
    score = best_service.base_complexity_points + factor_points
    missing_information = detect_missing_information(extraction, business_config)

    return ComplexityAssessment(
        level=_level_for_score(score, business_config),
        score=score,
        factors=extraction.complexity_factors,
        unknowns=[item.field_id for item in missing_information],
    )
