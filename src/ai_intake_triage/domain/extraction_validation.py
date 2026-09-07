"""Deterministic validation of untrusted AI extraction candidates."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from ai_intake_triage.configuration.business import BusinessConfig
from ai_intake_triage.domain.enums import ValidationIssueCode
from ai_intake_triage.domain.evidence import (
    evidence_is_traceable,
    normalize_evidence_text,
)
from ai_intake_triage.domain.extraction import AIExtraction
from ai_intake_triage.domain.triage import ValidationIssue


class EvidenceBearingItem(Protocol):
    """Provider-generated item containing evidence to verify."""

    evidence: list[str]


@dataclass(frozen=True, slots=True)
class ExtractionValidationResult:
    """Extraction candidates retained after one deterministic validation stage."""

    extraction: AIExtraction
    validation_issues: list[ValidationIssue]


def _retain_traceable_items[EvidenceItem: EvidenceBearingItem](
    items: Sequence[EvidenceItem],
    *,
    inquiry_text: str,
    item_type: str,
    reference_for: Callable[[EvidenceItem], str],
) -> tuple[list[EvidenceItem], list[ValidationIssue]]:
    """Keep items whose every evidence excerpt occurs in the inquiry."""
    accepted: list[EvidenceItem] = []
    issues: list[ValidationIssue] = []

    for item in items:
        untraceable = next(
            (
                excerpt
                for excerpt in item.evidence
                if not evidence_is_traceable(inquiry_text, excerpt)
            ),
            None,
        )

        if untraceable is None:
            accepted.append(item)
            continue

        issues.append(
            ValidationIssue(
                code=ValidationIssueCode.UNTRACEABLE_EVIDENCE,
                item_type=item_type,
                item_reference=reference_for(item),
                message=f"Evidence excerpt is not traceable to the inquiry: {untraceable!r}",
            )
        )

    return accepted, issues


def validate_extraction_evidence(
    extraction: AIExtraction,
    inquiry_text: str,
) -> ExtractionValidationResult:
    """Reject evidence-backed candidates that cannot be traced to the inquiry."""
    updates: dict[str, object] = {}
    validation_issues: list[ValidationIssue] = []

    collections = (
        ("stated_requirements", "stated_requirement", lambda item: item.statement),
        ("mentioned_systems", "mentioned_system", lambda item: item.name),
        ("intake_field_findings", "intake_field_finding", lambda item: item.field_id),
        ("service_candidates", "service_candidate", lambda item: item.service_id),
        ("complexity_factors", "complexity_factor", lambda item: item.factor_id),
        ("ambiguities", "ambiguity", lambda item: item.description),
        ("contradictions", "contradiction", lambda item: item.description),
    )

    for field_name, item_type, reference_for in collections:
        accepted, issues = _retain_traceable_items(
            getattr(extraction, field_name),
            inquiry_text=inquiry_text,
            item_type=item_type,
            reference_for=reference_for,
        )
        updates[field_name] = accepted
        validation_issues.extend(issues)

    return ExtractionValidationResult(
        extraction=extraction.model_copy(update=updates),
        validation_issues=validation_issues,
    )


def _retain_supported_references[ReferenceItem](
    items: Sequence[ReferenceItem],
    *,
    supported_ids: set[str],
    item_type: str,
    reference_for: Callable[[ReferenceItem], str],
) -> tuple[list[ReferenceItem], list[ValidationIssue]]:
    """Keep items whose referenced identifier exists in configuration."""
    accepted: list[ReferenceItem] = []
    issues: list[ValidationIssue] = []

    for item in items:
        reference = reference_for(item)
        if reference in supported_ids:
            accepted.append(item)
            continue

        issues.append(
            ValidationIssue(
                code=ValidationIssueCode.UNSUPPORTED_REFERENCE,
                item_type=item_type,
                item_reference=reference,
                message=f"Referenced ID is not present in business configuration: {reference!r}",
            )
        )

    return accepted, issues


def validate_extraction_references(
    extraction: AIExtraction,
    business_config: BusinessConfig,
) -> ExtractionValidationResult:
    """Reject extraction candidates that reference undeclared catalog IDs."""
    intake_field_ids = {field.id for field in business_config.intake_fields}
    service_ids = {service.id for service in business_config.services}
    complexity_factor_ids = {factor.id for factor in business_config.complexity.factors}

    collections = (
        (
            "intake_field_findings",
            "intake_field_finding",
            intake_field_ids,
            lambda item: item.field_id,
        ),
        (
            "service_candidates",
            "service_candidate",
            service_ids,
            lambda item: item.service_id,
        ),
        (
            "complexity_factors",
            "complexity_factor",
            complexity_factor_ids,
            lambda item: item.factor_id,
        ),
        (
            "draft_questions",
            "draft_clarifying_question",
            intake_field_ids,
            lambda item: item.field_id,
        ),
    )

    updates: dict[str, object] = {}
    validation_issues: list[ValidationIssue] = []

    for field_name, item_type, supported_ids, reference_for in collections:
        accepted, issues = _retain_supported_references(
            getattr(extraction, field_name),
            supported_ids=supported_ids,
            item_type=item_type,
            reference_for=reference_for,
        )
        updates[field_name] = accepted
        validation_issues.extend(issues)

    return ExtractionValidationResult(
        extraction=extraction.model_copy(update=updates),
        validation_issues=validation_issues,
    )


def _remove_duplicate_items[DuplicateItem](
    items: Sequence[DuplicateItem],
    *,
    item_type: str,
    identity_for: Callable[[DuplicateItem], str],
) -> tuple[list[DuplicateItem], list[ValidationIssue]]:
    """Keep the first item for each deterministic identity."""
    accepted: list[DuplicateItem] = []
    issues: list[ValidationIssue] = []
    seen: set[str] = set()

    for item in items:
        identity = identity_for(item)
        if identity not in seen:
            seen.add(identity)
            accepted.append(item)
            continue

        issues.append(
            ValidationIssue(
                code=ValidationIssueCode.DUPLICATE_ITEM,
                item_type=item_type,
                item_reference=identity,
                message=f"A later item duplicates an earlier candidate: {identity!r}",
            )
        )

    return accepted, issues


def validate_extraction_duplicates(
    extraction: AIExtraction,
) -> ExtractionValidationResult:
    """Remove exact normalized duplicates within one extraction."""
    normalized = normalize_evidence_text
    collections = (
        (
            "stated_requirements",
            "stated_requirement",
            lambda item: normalized(item.statement),
        ),
        (
            "mentioned_systems",
            "mentioned_system",
            lambda item: normalized(item.name),
        ),
        (
            "intake_field_findings",
            "intake_field_finding",
            lambda item: item.field_id,
        ),
        (
            "inferred_capabilities",
            "inferred_capability",
            lambda item: normalized(item.capability),
        ),
        (
            "service_candidates",
            "service_candidate",
            lambda item: item.service_id,
        ),
        (
            "complexity_factors",
            "complexity_factor",
            lambda item: item.factor_id,
        ),
        (
            "ambiguities",
            "ambiguity",
            lambda item: normalized(item.description),
        ),
        (
            "contradictions",
            "contradiction",
            lambda item: normalized(item.description),
        ),
        (
            "draft_questions",
            "draft_clarifying_question",
            lambda item: item.field_id,
        ),
    )

    updates: dict[str, object] = {}
    validation_issues: list[ValidationIssue] = []

    for field_name, item_type, identity_for in collections:
        accepted, issues = _remove_duplicate_items(
            getattr(extraction, field_name),
            item_type=item_type,
            identity_for=identity_for,
        )
        updates[field_name] = accepted
        validation_issues.extend(issues)

    return ExtractionValidationResult(
        extraction=extraction.model_copy(update=updates),
        validation_issues=validation_issues,
    )
