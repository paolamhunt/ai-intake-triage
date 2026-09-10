"""Assembly of trusted triage results from untrusted AI extraction output."""

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.complexity import assess_complexity
from ai_intake_triage.domain.extraction import AIExtraction
from ai_intake_triage.domain.extraction_validation import validate_extraction
from ai_intake_triage.domain.human_review import build_human_review_requirement
from ai_intake_triage.domain.missing_information import detect_missing_information
from ai_intake_triage.domain.routing import recommend_next_action
from ai_intake_triage.domain.service_ranking import rank_service_candidates
from ai_intake_triage.domain.triage import TriageResult


def build_triage_result(
    extraction: AIExtraction,
    *,
    inquiry_text: str,
    business_config: BusinessConfig,
) -> TriageResult:
    """Validate AI output and apply deterministic triage rules."""
    validation = validate_extraction(
        extraction,
        inquiry_text=inquiry_text,
        business_config=business_config,
    )
    validated_extraction = validation.extraction.model_copy(
        update={
            "service_candidates": rank_service_candidates(
                validation.extraction.service_candidates
            )
        }
    )

    missing_information = detect_missing_information(
        validated_extraction,
        business_config,
    )
    complexity = assess_complexity(validated_extraction, business_config)
    recommended_action = recommend_next_action(
        validated_extraction,
        business_config,
        missing_information=missing_information,
    )
    human_review = build_human_review_requirement(
        validated_extraction,
        business_config,
        missing_information=missing_information,
        validation_issues=validation.validation_issues,
    )

    return TriageResult(
        summary=validated_extraction.summary,
        primary_pain_point=validated_extraction.primary_pain_point,
        stated_requirements=validated_extraction.stated_requirements,
        mentioned_systems=validated_extraction.mentioned_systems,
        intake_field_findings=validated_extraction.intake_field_findings,
        inferred_capabilities=validated_extraction.inferred_capabilities,
        service_candidates=validated_extraction.service_candidates,
        missing_information=missing_information,
        complexity=complexity,
        ambiguities=validated_extraction.ambiguities,
        contradictions=validated_extraction.contradictions,
        recommended_action=recommended_action,
        human_review=human_review,
        validation_issues=validation.validation_issues,
    )
