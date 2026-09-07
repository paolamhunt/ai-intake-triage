"""Validated models for business-specific intake configuration."""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_intake_triage.domain.enums import ServiceMatchLevel
from ai_intake_triage.domain.types import NonEmptyText, StableIdentifier


def find_duplicates(values: list[str]) -> set[str]:
    """Return values that occur more than once."""
    seen: set[str] = set()
    duplicates: set[str] = set()

    for value in values:
        if value in seen:
            duplicates.add(value)
        else:
            seen.add(value)

    return duplicates


class ConfigurationModel(BaseModel):
    """Strict immutable base for trusted business configuration."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        frozen=True,
    )


class BusinessProfile(ConfigurationModel):
    """Identity and context for the configured business."""

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2_000)


class IntakeFieldConfig(ConfigurationModel):
    """Reusable information that may be needed to understand an inquiry."""

    id: StableIdentifier
    description: str = Field(min_length=1, max_length=500)
    default_question: str = Field(min_length=1, max_length=500)


class ServiceConfig(ConfigurationModel):
    """One service offered by the configured business."""

    id: StableIdentifier
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2_000)
    typical_capabilities: list[NonEmptyText] = Field(min_length=1)
    required_information: list[StableIdentifier] = Field(min_length=1)
    optional_information: list[StableIdentifier] = Field(default_factory=list)
    base_complexity_points: int = Field(ge=0, le=10)

    @model_validator(mode="after")
    def validate_information_references(self) -> Self:
        """Reject duplicate and contradictory field references."""
        required_duplicates = find_duplicates(self.required_information)
        optional_duplicates = find_duplicates(self.optional_information)
        overlap = set(self.required_information) & set(self.optional_information)

        if required_duplicates:
            raise ValueError(
                "required_information contains duplicate field IDs: "
                f"{sorted(required_duplicates)}"
            )
        if optional_duplicates:
            raise ValueError(
                "optional_information contains duplicate field IDs: "
                f"{sorted(optional_duplicates)}"
            )
        if overlap:
            raise ValueError(
                f"Information cannot be both required and optional: {sorted(overlap)}"
            )

        return self


class ComplexityFactorConfig(ConfigurationModel):
    """A configured factor contributing to preliminary complexity."""

    id: StableIdentifier
    description: str = Field(min_length=1, max_length=500)
    points: int = Field(ge=1, le=10)


class ComplexityThresholds(ConfigurationModel):
    """Maximum scores for low and medium complexity."""

    low_max: int = Field(ge=0)
    medium_max: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_threshold_order(self) -> Self:
        """Require a non-overlapping increasing threshold sequence."""
        if self.low_max >= self.medium_max:
            raise ValueError("low_max must be less than medium_max.")

        return self


class ComplexityConfig(ConfigurationModel):
    """Factors and thresholds used for deterministic complexity scoring."""

    factors: list[ComplexityFactorConfig] = Field(min_length=1)
    thresholds: ComplexityThresholds


class RoutingConfig(ConfigurationModel):
    """Narrowly configurable options for deterministic routing."""

    discovery_match_levels: list[ServiceMatchLevel] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_discovery_match_levels(self) -> Self:
        """Prevent duplicate or unsafe discovery-eligible match levels."""
        if len(self.discovery_match_levels) != len(set(self.discovery_match_levels)):
            raise ValueError("discovery_match_levels contains duplicates.")
        if ServiceMatchLevel.WEAK in self.discovery_match_levels:
            raise ValueError("A weak service match cannot be eligible for discovery.")

        return self


class BusinessConfig(ConfigurationModel):
    """Complete configuration for one running application instance."""

    version: str = Field(min_length=1, max_length=50)
    business: BusinessProfile
    intake_fields: list[IntakeFieldConfig] = Field(min_length=1)
    services: list[ServiceConfig] = Field(min_length=1)
    supported_technologies: list[NonEmptyText] = Field(default_factory=list)
    complexity: ComplexityConfig
    routing: RoutingConfig

    @model_validator(mode="after")
    def validate_catalogs_and_references(self) -> Self:
        """Reject duplicate IDs and references to undeclared catalog items."""
        intake_field_ids = [field.id for field in self.intake_fields]
        service_ids = [service.id for service in self.services]
        complexity_factor_ids = [factor.id for factor in self.complexity.factors]

        duplicate_catalogs = {
            "intake_fields": find_duplicates(intake_field_ids),
            "services": find_duplicates(service_ids),
            "complexity.factors": find_duplicates(complexity_factor_ids),
        }
        for catalog, duplicates in duplicate_catalogs.items():
            if duplicates:
                raise ValueError(
                    f"{catalog} contains duplicate IDs: {sorted(duplicates)}"
                )

        declared_fields = set(intake_field_ids)
        for service in self.services:
            referenced_fields = set(service.required_information)
            referenced_fields.update(service.optional_information)
            unknown_fields = referenced_fields - declared_fields

            if unknown_fields:
                raise ValueError(
                    f"Service '{service.id}' references unknown intake "
                    f"field IDs: {sorted(unknown_fields)}"
                )

        return self
