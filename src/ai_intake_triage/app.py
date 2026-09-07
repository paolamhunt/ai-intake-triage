"""FastAPI application factory."""

from fastapi import FastAPI

from ai_intake_triage.configuration.loader import load_business_config
from ai_intake_triage.configuration.settings import AppSettings


def create_app(settings: AppSettings) -> FastAPI:
    """Create an application using validated settings."""
    documentation_url = "/docs" if settings.documentation_enabled else None
    redoc_url = "/redoc" if settings.documentation_enabled else None
    openapi_url = "/openapi.json" if settings.documentation_enabled else None
    business_config = load_business_config(settings.business_config_path)

    app = FastAPI(
        title="AI Intake Triage",
        version="0.1.0",
        docs_url=documentation_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    app.state.business_config = business_config

    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        """Report whether the application is running."""
        return {"status": "ok"}

    return app
