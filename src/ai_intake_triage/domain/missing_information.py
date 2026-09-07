"""Deterministic detection of required information missing from an inquiry."""

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import InformationPriority
from ai_intake_triage.domain.extraction import AIExtraction
from ai_intake_triage.domain.service_ranking import rank_service_candidates
from ai_intake_triage.domain.triage import MissingInformation


def detect_missing_information(
    extraction: AIExtraction,
    business_config: BusinessConfig,
) -> list[MissingInformation]:
    """Find required fields missing for the best validated service candidate."""
    ranked_candidates = rank_service_candidates(extraction.service_candidates)
    if not ranked_candidates:
        return []

    best_candidate = ranked_candidates[0]
    service_by_id = {service.id: service for service in business_config.services}
    field_by_id = {field.id: field for field in business_config.intake_fields}
    best_service = service_by_id[best_candidate.service_id]

    present_field_ids = {
        finding.field_id for finding in extraction.intake_field_findings
    }
    question_by_field_id: dict[str, str] = {}
    for draft in extraction.draft_questions:
        question_by_field_id.setdefault(draft.field_id, draft.question)

    missing: list[MissingInformation] = []
    for field_id in best_service.required_information:
        if field_id in present_field_ids:
            continue

        field_config = field_by_id[field_id]
        missing.append(
            MissingInformation(
                field_id=field_id,
                priority=InformationPriority.REQUIRED,
                reason=(
                    f"Required to assess the {best_service.name} service candidate."
                ),
                question=question_by_field_id.get(
                    field_id,
                    field_config.default_question,
                ),
            )
        )

    return missing
