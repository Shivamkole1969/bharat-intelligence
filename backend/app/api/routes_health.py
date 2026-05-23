"""
Bharat Market Intelligence Agent — Health & System Routes

Provides health check, readiness probe, and system status endpoints.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.schemas import HealthResponse
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Health check endpoint.
    Verifies database connectivity and returns system status.
    """
    services: dict = {}

    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        services["database"] = "healthy"
    except Exception as e:
        logger.error("Database health check failed: %s", str(e))
        services["database"] = "unhealthy"

    # Check Redis (will be implemented when Redis service is added)
    # TODO(infra): Add Redis health check
    services["redis"] = "not_configured"

    # Check Kafka/Redpanda (will be implemented when streaming is added)
    # TODO(infra): Add Kafka health check
    services["kafka"] = "not_configured"

    overall_status = "healthy" if services.get("database") == "healthy" else "degraded"

    return HealthResponse(
        status=overall_status,
        app_name=settings.app_name,
        version="0.1.0",
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc),
        services=services,
    )


@router.get("/ready")
async def readiness_probe(db: AsyncSession = Depends(get_db)) -> dict:
    """Kubernetes readiness probe — checks if the app can serve traffic."""
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {"ready": True}
    except Exception:
        return {"ready": False}


@router.get("/live")
async def liveness_probe() -> dict:
    """Kubernetes liveness probe — checks if the process is alive."""
    return {"alive": True}
