"""Constrained vocabulary shared across the domain."""

from enum import StrEnum


class ServiceMatchLevel(StrEnum):
    """Strength of an AI-suggested configured service match."""

    STRONG = "strong"
    POSSIBLE = "possible"
    WEAK = "weak"
