"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(
    title="AI Intake Triage",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report whether the application is running."""
    return {"status": "ok"}
