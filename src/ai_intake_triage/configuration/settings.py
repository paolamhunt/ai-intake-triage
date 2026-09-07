"""Typed application settings loaded from the environment."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Validated settings for one application instance."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="AIT_",
        extra="ignore",
        frozen=True,
    )

    environment: Literal["development", "test", "production"] = "development"
    operator_api_key: SecretStr = Field(min_length=32)
    business_config_path: Path = Path("configs/the_distracted_developer.yaml")

    @property
    def documentation_enabled(self) -> bool:
        """Allow interactive API documentation only during development."""
        return self.environment == "development"
