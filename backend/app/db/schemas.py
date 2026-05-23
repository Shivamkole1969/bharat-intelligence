"""
Bharat Market Intelligence Agent — Pydantic Schemas

Request/response models for API endpoints.
Separates internal DB models from API contracts.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# Company Schemas
# ============================================================
class CompanyBase(BaseModel):
    symbol: str
    exchange: str
    company_name: str
    isin: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    website: Optional[str] = None
    bse_code: Optional[str] = None
    nse_symbol: Optional[str] = None
    is_active: bool = True


class CompanyResponse(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CompanyListResponse(BaseModel):
    total: int
    companies: List[CompanyResponse]


# ============================================================
# Market Event Schemas
# ============================================================
class EventCitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    citation_text: Optional[str] = None
    source_url: Optional[str] = None
    page_number: Optional[int] = None
    confidence_score: Optional[float] = None


class MarketEventBase(BaseModel):
    event_type: str
    event_subtype: Optional[str] = None
    event_title: str
    event_summary: Optional[str] = None
    impact_label: Optional[str] = None
    impact_score: Optional[float] = None
    confidence_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    severity: Optional[str] = None
    source_url: Optional[str] = None
    is_material: bool = False


class MarketEventResponse(MarketEventBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    event_time: Optional[datetime] = None
    detected_at: datetime
    entities: Optional[dict] = None
    metrics: Optional[dict] = None
    is_duplicate: bool = False
    created_at: datetime
    citations: List[EventCitationResponse] = []

    # Populated via join
    company_symbol: Optional[str] = None
    company_name: Optional[str] = None


class MarketEventListResponse(BaseModel):
    total: int
    events: List[MarketEventResponse]


# ============================================================
# Chat Schemas
# ============================================================
class UserAPIConfig(BaseModel):
    """User-provided API key configuration for LLM calls."""
    provider: str = Field(..., description="Provider: groq, openai, anthropic, gemini")
    api_key: str = Field(..., min_length=5, description="API key")
    model: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    mode: str = Field(default="general_market")
    company_symbol: Optional[str] = None
    session_id: Optional[uuid.UUID] = None
    user_api_config: Optional[UserAPIConfig] = None


class CitationItem(BaseModel):
    source: str
    published_at: Optional[str] = None
    snippet: str
    url: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    citations: List[CitationItem] = []
    confidence: str = "medium"
    limitations: Optional[str] = None
    disclaimer: str = (
        "This is informational and not investment advice. "
        "Please verify independently and consult a SEBI-registered adviser."
    )
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    session_id: Optional[uuid.UUID] = None
    cached: bool = False


# ============================================================
# Signal / Thesis Schemas
# ============================================================
class SignalScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    score_date: date
    bullish_score: float
    bearish_score: float
    quality_score: float
    momentum_score: float
    confidence_score: float
    explanation: Optional[str] = None
    top_positive_factors: List[str] = []
    top_negative_factors: List[str] = []

    # Populated via join
    company_symbol: Optional[str] = None
    company_name: Optional[str] = None
    sector: Optional[str] = None


class BullishListResponse(BaseModel):
    generated_at: datetime
    disclaimer: str = (
        "These are signal candidates for research, not buy recommendations. "
        "This is not investment advice."
    )
    candidates: List[SignalScoreResponse]


class BearishListResponse(BaseModel):
    generated_at: datetime
    disclaimer: str = (
        "These are risk candidates for research, not short-selling recommendations. "
        "This is not investment advice."
    )
    candidates: List[SignalScoreResponse]


class ThesisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    thesis_type: str
    thesis_title: str
    thesis_summary: str
    supporting_points: List[str] = []
    risks: List[str] = []
    counterpoints: List[str] = []
    citations: List[dict] = []
    confidence_score: Optional[float] = None
    generated_by_model: Optional[str] = None
    generated_at: datetime

    # Populated via join
    company_symbol: Optional[str] = None
    company_name: Optional[str] = None


# ============================================================
# Watchlist Schemas
# ============================================================
class WatchlistCompanyAdd(BaseModel):
    company_id: uuid.UUID
    alert_threshold: str = "medium"


class WatchlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    companies: List[WatchlistCompanyAdd] = []


class WatchlistCompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: Optional[uuid.UUID] = None
    alert_threshold: str
    company_symbol: Optional[str] = None
    company_name: Optional[str] = None


class WatchlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime
    companies: List[WatchlistCompanyResponse] = []


# ============================================================
# Health & System Schemas
# ============================================================
class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str = "0.1.0"
    environment: str
    timestamp: datetime
    services: dict = {}


class MarketSummaryResponse(BaseModel):
    generated_at: datetime
    total_events_today: int = 0
    positive_events: int = 0
    negative_events: int = 0
    neutral_events: int = 0
    top_sectors: List[dict] = []
    latest_events: List[MarketEventResponse] = []
    disclaimer: str = "This summary is for informational purposes only."
