"""FastAPI application entry point."""

from ai_intake_triage.app import create_app
from ai_intake_triage.configuration.settings import AppSettings

app = create_app(AppSettings())
