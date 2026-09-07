"""Constrained vocabulary shared across the intake-triage domain."""

from enum import StrEnum


class ServiceMatchLevel(StrEnum):
    """Strength of a proposed match to a configured service."""

    STRONG = "strong"
    POSSIBLE = "possible"
    WEAK = "weak"


class ComplexityLevel(StrEnum):
    """Preliminary complexity assigned by deterministic scoring."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class RecommendedAction(StrEnum):
    """Constrained next actions selected by deterministic routing."""

    REQUEST_MORE_INFORMATION = "request_more_information"
    PROCEED_TO_DISCOVERY = "proceed_to_discovery"
    MANUAL_ASSESSMENT = "manual_assessment"
    REVIEW_SERVICE_MISMATCH = "review_service_mismatch"
    RETRY_PROCESSING = "retry_processing"


class InformationPriority(StrEnum):
    """Whether missing information blocks discovery for a service."""

    REQUIRED = "required"
    OPTIONAL = "optional"


class ValidationIssueCode(StrEnum):
    """Reasons provider-generated items were not trusted."""

    UNTRACEABLE_EVIDENCE = "untraceable_evidence"
    UNSUPPORTED_REFERENCE = "unsupported_reference"
    DUPLICATE_ITEM = "duplicate_item"
