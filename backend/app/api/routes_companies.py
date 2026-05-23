"""
Bharat Market Intelligence Agent — Company Routes

CRUD and search endpoints for company data.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company
from app.db.schemas import CompanyListResponse, CompanyResponse
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    search: Optional[str] = Query(None, description="Search by name or symbol"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=600, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
) -> CompanyListResponse:
    """List companies with optional filtering and pagination."""
    query = select(Company).where(Company.is_active == is_active)

    if sector:
        query = query.where(Company.sector == sector)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Company.company_name.ilike(search_pattern))
            | (Company.symbol.ilike(search_pattern))
            | (Company.nse_symbol.ilike(search_pattern))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    query = query.order_by(Company.company_name).limit(limit).offset(offset)
    result = await db.execute(query)
    companies = result.scalars().all()

    return CompanyListResponse(
        total=total,
        companies=[CompanyResponse.model_validate(c) for c in companies],
    )


@router.get("/sectors")
async def list_sectors(db: AsyncSession = Depends(get_db)) -> dict:
    """Get all unique sectors with company counts."""
    query = (
        select(Company.sector, func.count(Company.id).label("count"))
        .where(Company.is_active == True)  # noqa: E712
        .where(Company.sector.is_not(None))
        .group_by(Company.sector)
        .order_by(func.count(Company.id).desc())
    )
    result = await db.execute(query)
    rows = result.all()

    return {
        "sectors": [
            {"sector": row.sector, "count": row.count} for row in rows
        ]
    }


@router.get("/{symbol}", response_model=CompanyResponse)
async def get_company(
    symbol: str,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    """Get company details by symbol (NSE symbol lookup)."""
    query = select(Company).where(
        (Company.symbol == symbol.upper())
        | (Company.nse_symbol == symbol.upper())
    )
    result = await db.execute(query)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return CompanyResponse.model_validate(company)
