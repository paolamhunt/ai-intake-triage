"""Structured candidate output produced by an AI provider."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from ai_intake_triage.domain.enums import ServiceMatchLevel
from ai_intake_triage.domain.types import StableIdentifier

EvidenceExcerpt = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=5,
        max_length=300,
    ),
]


class ExtractionModel(BaseModel):
    """Strict immutable base for provider-generated candidate data."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        frozen=True,
    )


class EvidenceBackedStatement(ExtractionModel):
    """A statement claimed to be explicit in the original inquiry."""

    statement: str = Field(min_length=1, max_length=1_000)
    evidence: list[EvidenceExcerpt] = Field(min_length=1, max_length=5)


class MentionedSystem(ExtractionModel):
    """A system or technology claimed to be named in the inquiry."""

    name: str = Field(min_length=1, max_length=200)
    evidence: list[EvidenceExcerpt] = Field(min_length=1, max_length=5)


class IntakeFieldFinding(ExtractionModel):
    """Evidence that a configured intake field is present in the inquiry."""

    field_id: StableIdentifier
    value: str = Field(min_length=1, max_length=1_000)
    evidence: list[EvidenceExcerpt] = Field(min_length=1, max_length=5)


class InferredCapability(ExtractionModel):
    """A possible capability that is not explicitly confirmed by the client."""

    capability: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=500)


class ServiceCandidate(ExtractionModel):
    """A possible configured service match proposed by the AI."""

    service_id: StableIdentifier
    match_level: ServiceMatchLevel
    reason: str = Field(min_length=1, max_length=500)
    evidence: list[EvidenceExcerpt] = Field(min_length=1, max_length=5)


class ComplexityFactorCandidate(ExtractionModel):
    """A configured complexity factor claimed to apply to the inquiry."""

    factor_id: StableIdentifier
    reason: str = Field(min_length=1, max_length=500)
    evidence: list[EvidenceExcerpt] = Field(min_length=1, max_length=5)


class Ambiguity(ExtractionModel):
    """Materially unclear language found in the inquiry."""

    description: str = Field(min_length=1, max_length=500)
    evidence: list[EvidenceExcerpt] = Field(min_length=1, max_length=5)


class Contradiction(ExtractionModel):
    """Two or more conflicting statements found in the inquiry."""

    description: str = Field(min_length=1, max_length=500)
    evidence: list[EvidenceExcerpt] = Field(min_length=2, max_length=5)


class DraftClarifyingQuestion(ExtractionModel):
    """A customer-friendly question proposed for a configured intake field."""

    field_id: StableIdentifier
    question: str = Field(min_length=1, max_length=500)


class AIExtraction(ExtractionModel):
    """Untrusted structured candidate output returned by an AI provider."""

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
    complexity_factors: list[ComplexityFactorCandidate] = Field(
        default_factory=list,
        max_length=20,
    )
    ambiguities: list[Ambiguity] = Field(
        default_factory=list,
        max_length=10,
    )
    contradictions: list[Contradiction] = Field(
        default_factory=list,
        max_length=10,
    )
    draft_questions: list[DraftClarifyingQuestion] = Field(
        default_factory=list,
        max_length=25,
    )
