"""
Bharat Market Intelligence Agent — Market Event Routes

Endpoints for latest events, company events, sector events, and market summary.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Company, MarketEvent
from app.db.schemas import (
    MarketEventListResponse,
    MarketEventResponse,
    MarketSummaryResponse,
)
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/events", tags=["Events"])


def _event_to_response(event: MarketEvent) -> MarketEventResponse:
    """Convert MarketEvent ORM model to response schema with company info."""
    data = MarketEventResponse.model_validate(event)
    if event.company:
        data.company_symbol = event.company.symbol
        data.company_name = event.company.company_name
    return data


@router.get("/latest", response_model=MarketEventListResponse)
async def get_latest_events(
    impact: Optional[str] = Query(
        None, description="Filter by impact: positive, negative, neutral"
    ),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    hours: int = Query(24, ge=1, le=168, description="Lookback hours"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> MarketEventListResponse:
    """Get latest market events across all companies."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)

    query = (
        select(MarketEvent)
        .options(selectinload(MarketEvent.company))
        .options(selectinload(MarketEvent.citations))
        .where(MarketEvent.is_duplicate == False)  # noqa: E712
        .where(MarketEvent.detected_at >= cutoff)
    )

    if impact:
        query = query.where(MarketEvent.impact_label == impact.lower())
    if event_type:
        query = query.where(MarketEvent.event_type == event_type)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch
    query = (
        query.order_by(MarketEvent.detected_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    events = result.scalars().unique().all()

    return MarketEventListResponse(
        total=total,
        events=[_event_to_response(e) for e in events],
    )


@router.get("/company/{symbol}", response_model=MarketEventListResponse)
async def get_company_events(
    symbol: str,
    days: int = Query(7, ge=1, le=90, description="Lookback days"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> MarketEventListResponse:
    """Get market events for a specific company."""
    # Find company
    company_query = select(Company).where(
        (Company.symbol == symbol.upper())
        | (Company.nse_symbol == symbol.upper())
    )
    company_result = await db.execute(company_query)
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    query = (
        select(MarketEvent)
        .options(selectinload(MarketEvent.company))
        .options(selectinload(MarketEvent.citations))
        .where(MarketEvent.company_id == company.id)
        .where(MarketEvent.is_duplicate == False)  # noqa: E712
        .where(MarketEvent.detected_at >= cutoff)
    )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        query.order_by(MarketEvent.detected_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    events = result.scalars().unique().all()

    return MarketEventListResponse(
        total=total,
        events=[_event_to_response(e) for e in events],
    )


@router.get("/sector/{sector}", response_model=MarketEventListResponse)
async def get_sector_events(
    sector: str,
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> MarketEventListResponse:
    """Get market events for a specific sector."""
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)

    query = (
        select(MarketEvent)
        .join(Company, MarketEvent.company_id == Company.id)
        .options(selectinload(MarketEvent.company))
        .options(selectinload(MarketEvent.citations))
        .where(Company.sector == sector)
        .where(MarketEvent.is_duplicate == False)  # noqa: E712
        .where(MarketEvent.detected_at >= cutoff)
    )

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = (
        query.order_by(MarketEvent.detected_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    events = result.scalars().unique().all()

    return MarketEventListResponse(
        total=total,
        events=[_event_to_response(e) for e in events],
    )


@router.get("/summary", response_model=MarketSummaryResponse)
async def get_market_summary(
    db: AsyncSession = Depends(get_db),
) -> MarketSummaryResponse:
    """Get today's market intelligence summary."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=None
    )

    base_query = select(MarketEvent).where(
        MarketEvent.detected_at >= today_start,
        MarketEvent.is_duplicate == False,  # noqa: E712
    )

    # Total events today
    total_result = await db.execute(
        select(func.count()).select_from(base_query.subquery())
    )
    total = total_result.scalar() or 0

    # Count by impact
    impact_counts = {}
    for label in ["positive", "negative", "neutral"]:
        impact_query = select(func.count()).select_from(
            base_query.where(MarketEvent.impact_label == label).subquery()
        )
        result = await db.execute(impact_query)
        impact_counts[label] = result.scalar() or 0

    # Top sectors by event count
    sector_query = (
        select(Company.sector, func.count(MarketEvent.id).label("event_count"))
        .join(Company, MarketEvent.company_id == Company.id)
        .where(MarketEvent.detected_at >= today_start)
        .where(MarketEvent.is_duplicate == False)  # noqa: E712
        .where(Company.sector.is_not(None))
        .group_by(Company.sector)
        .order_by(func.count(MarketEvent.id).desc())
        .limit(10)
    )
    sector_result = await db.execute(sector_query)
    top_sectors = [
        {"sector": row.sector, "event_count": row.event_count}
        for row in sector_result.all()
    ]

    # Latest 10 events
    latest_query = (
        select(MarketEvent)
        .options(selectinload(MarketEvent.company))
        .options(selectinload(MarketEvent.citations))
        .where(MarketEvent.is_duplicate == False)  # noqa: E712
        .order_by(MarketEvent.detected_at.desc())
        .limit(10)
    )
    latest_result = await db.execute(latest_query)
    latest_events = latest_result.scalars().unique().all()

    return MarketSummaryResponse(
        generated_at=datetime.now(timezone.utc),
        total_events_today=total,
        positive_events=impact_counts.get("positive", 0),
        negative_events=impact_counts.get("negative", 0),
        neutral_events=impact_counts.get("neutral", 0),
        top_sectors=top_sectors,
        latest_events=[_event_to_response(e) for e in latest_events],
    )
