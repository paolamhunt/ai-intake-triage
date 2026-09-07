"""Deterministic validation of untrusted AI extraction candidates."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol, TypeVar

from ai_intake_triage.domain.enums import ValidationIssueCode
from ai_intake_triage.domain.evidence import evidence_is_traceable
from ai_intake_triage.domain.extraction import AIExtraction
from ai_intake_triage.domain.triage import ValidationIssue


class EvidenceBearingItem(Protocol):
    """Provider-generated item containing evidence to verify."""

    evidence: list[str]


EvidenceItem = TypeVar("EvidenceItem", bound=EvidenceBearingItem)


@dataclass(frozen=True, slots=True)
class EvidenceValidationResult:
    """Extraction candidates retained after evidence validation."""

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
) -> EvidenceValidationResult:
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

    return EvidenceValidationResult(
        extraction=extraction.model_copy(update=updates),
        validation_issues=validation_issues,
    )
