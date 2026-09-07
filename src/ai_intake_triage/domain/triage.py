"""Trusted triage result produced after deterministic validation."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_intake_triage.domain.enums import (
    ComplexityLevel,
    InformationPriority,
    RecommendedAction,
    ValidationIssueCode,
)
from ai_intake_triage.domain.extraction import (
    Ambiguity,
    ComplexityFactorCandidate,
    Contradiction,
    EvidenceBackedStatement,
    InferredCapability,
    IntakeFieldFinding,
    MentionedSystem,
    ServiceCandidate,
)
from ai_intake_triage.domain.types import StableIdentifier


class TriageModel(BaseModel):
    """Strict immutable base for trusted triage data."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        frozen=True,
    )


class MissingInformation(TriageModel):
    """A configured intake field not established by accepted evidence."""

    field_id: StableIdentifier
    priority: InformationPriority
    reason: str = Field(min_length=1, max_length=500)
    question: str = Field(min_length=1, max_length=500)


class ComplexityAssessment(TriageModel):
    """A preliminary complexity result calculated from configured rules."""

    level: ComplexityLevel
    score: int | None = Field(default=None, ge=0)
    factors: list[ComplexityFactorCandidate] = Field(
        default_factory=list,
        max_length=20,
    )
    unknowns: list[StableIdentifier] = Field(
        default_factory=list,
        max_length=25,
    )

    @model_validator(mode="after")
    def validate_score_presence(self) -> Self:
        """Use a score only when a complexity level can be assigned."""
        if self.level is ComplexityLevel.UNKNOWN and self.score is not None:
            raise ValueError("Unknown complexity cannot have a score.")
        if self.level is not ComplexityLevel.UNKNOWN and self.score is None:
            raise ValueError("Known complexity must have a score.")

        return self


class RecommendedNextAction(TriageModel):
    """A constrained workflow recommendation selected by application rules."""

    action: RecommendedAction
    reason: str = Field(min_length=1, max_length=500)


class HumanReviewRequirement(TriageModel):
    """Reasons a human must review the triage result."""

    required: Literal[True] = True
    reasons: list[str] = Field(min_length=1, max_length=20)


class ValidationIssue(TriageModel):
    """A provider-generated item rejected during deterministic validation."""

    code: ValidationIssueCode
    item_type: StableIdentifier
    item_reference: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    message: str = Field(min_length=1, max_length=500)


class TriageResult(TriageModel):
    """Validated, explainable output presented for human review."""

    summary: str = Field(min_length=1, max_length=1_000)
    primary_pain_point: str = Field(min_length=1, max_length=500)
    stated_requirements: list[EvidenceBackedStatement] = Field(
        default_factory=list,
        max_length=25,
    )
    mentioned_systems: list[MentionedSystem] = Field(
        default_factory=list,
        max_length=25,
    )
    intake_field_findings: list[IntakeFieldFinding] = Field(
        default_factory=list,
        max_length=25,
    )
    inferred_capabilities: list[InferredCapability] = Field(
        default_factory=list,
        max_length=25,
    )
    service_candidates: list[ServiceCandidate] = Field(
        default_factory=list,
        max_length=10,
    )
    missing_information: list[MissingInformation] = Field(
        default_factory=list,
        max_length=25,
    )
    complexity: ComplexityAssessment
    ambiguities: list[Ambiguity] = Field(
        default_factory=list,
        max_length=10,
    )
    contradictions: list[Contradiction] = Field(
        default_factory=list,
        max_length=10,
    )
    recommended_action: RecommendedNextAction
    human_review: HumanReviewRequirement
    validation_issues: list[ValidationIssue] = Field(
        default_factory=list,
        max_length=50,
    )
