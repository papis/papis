"""Health check endpoint for server readiness probes."""

from __future__ import annotations

from fastapi import APIRouter

from papis.server.models import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Check server health.

    Returns ``status`` set to ``ok`` when the server is up and running normally.
    """
    return HealthResponse(status="ok")
