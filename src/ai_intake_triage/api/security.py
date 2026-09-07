"""Authentication dependencies for protected API routes."""

from collections.abc import Callable
from secrets import compare_digest
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from ai_intake_triage.configuration.settings import AppSettings

_OPERATOR_API_KEY_HEADER = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def build_operator_auth(settings: AppSettings) -> Callable[[str | None], None]:
    """Build an API-key verifier bound to validated application settings."""
    expected_api_key = settings.operator_api_key.get_secret_value()

    def require_operator_api_key(
        provided_api_key: Annotated[
            str | None,
            Security(_OPERATOR_API_KEY_HEADER),
        ],
    ) -> None:
        """Reject requests without the configured operator API key."""
        if provided_api_key is None or not compare_digest(
            provided_api_key,
            expected_api_key,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API key.",
            )

    return require_operator_api_key
