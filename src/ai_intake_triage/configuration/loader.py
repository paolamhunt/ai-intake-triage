"""Safe loading and validation of business configuration."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ai_intake_triage.configuration.business import BusinessConfig


class BusinessConfigLoadError(Exception):
    """Raised when business configuration cannot be safely loaded."""


def load_business_config(path: Path) -> BusinessConfig:
    """Load a YAML file and validate it as trusted business configuration."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as error:
        raise BusinessConfigLoadError(
            f"Unable to read business configuration: {path}"
        ) from error

    try:
        raw_config: Any = yaml.safe_load(content)
    except yaml.YAMLError as error:
        raise BusinessConfigLoadError(
            f"Business configuration contains invalid YAML: {path}"
        ) from error

    if not isinstance(raw_config, dict):
        raise BusinessConfigLoadError(
            "Business configuration must contain a top-level mapping."
        )

    try:
        return BusinessConfig.model_validate(raw_config)
    except ValidationError as error:
        raise BusinessConfigLoadError(
            f"Business configuration failed validation: {path}"
        ) from error
