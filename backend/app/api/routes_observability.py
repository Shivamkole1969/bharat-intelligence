"""
Bharat Market Intelligence Agent — Observability API Routes

Endpoints for:
- /metrics (Prometheus format)
- /health/deep (full health check)
- /audit/verify (hash chain verification)
- /audit/logs (paginated audit log viewer)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Observability"])


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Export metrics in Prometheus text exposition format."""
    from app.services.metrics_service import metrics
    return metrics.to_prometheus()


@router.get("/metrics/json")
async def json_metrics():
    """Export metrics as JSON for dashboards."""
    from app.services.metrics_service import metrics
    return metrics.get_all()


@router.get("/health/deep")
async def deep_health_check(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Comprehensive health check across all subsystems.
    More detailed than the basic /health endpoint.
    """
    from app.services.health_monitor import run_full_health_check
    return await run_full_health_check(db)


@router.get("/audit/verify")
async def verify_audit_chain(
    limit: int = Query(default=1000, le=10000),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Verify the integrity of the audit log hash chain.
    Returns verification status and any broken links.
    """
    from app.services.audit_service import verify_audit_chain
    return await verify_audit_chain(db, limit=limit)


@router.get("/audit/logs")
async def get_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    actor_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Paginated audit log viewer with optional filters.
    """
    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if actor_type:
        query = query.where(AuditLog.actor_type == actor_type)

    # Count total
    count_query = select(func.count(AuditLog.id))
    if action:
        count_query = count_query.where(AuditLog.action == action)
    if entity_type:
        count_query = count_query.where(AuditLog.entity_type == entity_type)
    if actor_type:
        count_query = count_query.where(AuditLog.actor_type == actor_type)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    entries = result.scalars().all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "entries": [
            {
                "id": str(e.id),
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "action": e.action,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "current_hash": e.current_hash[:16] + "…" if e.current_hash else None,
                "metadata": e.metadata_json,
            }
            for e in entries
        ],
    }
