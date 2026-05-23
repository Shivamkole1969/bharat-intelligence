"""
Bharat Market Intelligence Agent — Signal Routes

Bullish/bearish signal watchlist endpoints.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Company, StockSignalScore, StockThesis
from app.db.schemas import (
    BearishListResponse,
    BullishListResponse,
    SignalScoreResponse,
    ThesisResponse,
)
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/signals", tags=["Signals"])


def _score_to_response(score: StockSignalScore) -> SignalScoreResponse:
    """Convert signal score ORM model to response with company info."""
    data = SignalScoreResponse.model_validate(score)
    if score.company:
        data.company_symbol = score.company.symbol
        data.company_name = score.company.company_name
        data.sector = score.company.sector
    return data


@router.get("/bullish/top", response_model=BullishListResponse)
async def get_top_bullish(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> BullishListResponse:
    """
    Get top bullish signal candidates.

    These are companies with the highest bullish scores based on
    public signals. This is NOT a buy recommendation.
    """
    query = (
        select(StockSignalScore)
        .join(Company, StockSignalScore.company_id == Company.id)
        .options(selectinload(StockSignalScore.company))
        .where(Company.is_active == True)  # noqa: E712
        .order_by(StockSignalScore.bullish_score.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    scores = result.scalars().unique().all()

    return BullishListResponse(
        generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        candidates=[_score_to_response(s) for s in scores],
    )


@router.get("/bearish/top", response_model=BearishListResponse)
async def get_top_bearish(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> BearishListResponse:
    """
    Get top bearish risk candidates.

    These are companies with the highest bearish risk scores based on
    public signals. This is NOT a short-selling recommendation.
    """
    query = (
        select(StockSignalScore)
        .join(Company, StockSignalScore.company_id == Company.id)
        .options(selectinload(StockSignalScore.company))
        .where(Company.is_active == True)  # noqa: E712
        .order_by(StockSignalScore.bearish_score.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    scores = result.scalars().unique().all()

    return BearishListResponse(
        generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        candidates=[_score_to_response(s) for s in scores],
    )


@router.get("/thesis/{symbol}")
async def get_company_thesis(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get bullish and bearish theses for a company."""
    # Find company
    company_query = select(Company).where(
        (Company.symbol == symbol.upper())
        | (Company.nse_symbol == symbol.upper())
    )
    company_result = await db.execute(company_query)
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get theses
    theses_query = (
        select(StockThesis)
        .where(StockThesis.company_id == company.id)
        .order_by(StockThesis.generated_at.desc())
    )
    result = await db.execute(theses_query)
    theses = result.scalars().all()

    bullish_theses = [
        ThesisResponse.model_validate(t) for t in theses if t.thesis_type == "bullish"
    ]
    bearish_theses = [
        ThesisResponse.model_validate(t) for t in theses if t.thesis_type == "bearish"
    ]

    # Add company info
    for thesis in bullish_theses + bearish_theses:
        thesis.company_symbol = company.symbol
        thesis.company_name = company.company_name

    return {
        "company": {
            "symbol": company.symbol,
            "name": company.company_name,
            "sector": company.sector,
        },
        "bullish_theses": bullish_theses,
        "bearish_theses": bearish_theses,
        "disclaimer": (
            "These theses are generated from public signals for research purposes. "
            "They are not investment advice or recommendations. "
            "Please verify independently and consult a SEBI-registered adviser."
        ),
    }
