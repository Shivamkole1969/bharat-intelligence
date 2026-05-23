"""
Bharat Market Intelligence Agent — SQLAlchemy ORM Models

All 19 tables mapped as async-compatible SQLAlchemy models.
Uses pgvector for embedding columns.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


# ============================================================
# 1. Company
# ============================================================
class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(Text, nullable=False)
    exchange: Mapped[str] = mapped_column(Text, nullable=False)
    isin: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    market_cap: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bse_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nse_symbol: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    raw_documents: Mapped[list["RawDocument"]] = relationship(back_populates="company")
    market_events: Mapped[list["MarketEvent"]] = relationship(back_populates="company")
    document_chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="company"
    )
    signal_scores: Mapped[list["StockSignalScore"]] = relationship(
        back_populates="company"
    )
    theses: Mapped[list["StockThesis"]] = relationship(back_populates="company")

    __table_args__ = (UniqueConstraint("exchange", "symbol"),)


# ============================================================
# 2. DataSource
# ============================================================
class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reliability_score: Mapped[Optional[float]] = mapped_column(
        Numeric, default=0.80
    )
    license_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    # Relationships
    raw_documents: Mapped[list["RawDocument"]] = relationship(
        back_populates="data_source"
    )


# ============================================================
# 3. RawDocument
# ============================================================
class RawDocument(Base):
    __tablename__ = "raw_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.id"), nullable=True
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    document_type: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    content_hash: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, default=dict
    )

    # Relationships
    company: Mapped[Optional["Company"]] = relationship(back_populates="raw_documents")
    data_source: Mapped[Optional["DataSource"]] = relationship(
        back_populates="raw_documents"
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    events: Mapped[list["MarketEvent"]] = relationship(
        back_populates="source_document"
    )
    citations: Mapped[list["EventCitation"]] = relationship(
        back_populates="document"
    )


# ============================================================
# 4. DocumentChunk
# ============================================================
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_documents.id", ondelete="CASCADE"),
        nullable=True,
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    embedding = mapped_column(Vector(384), nullable=True)
    section_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    # Relationships
    document: Mapped[Optional["RawDocument"]] = relationship(back_populates="chunks")
    company: Mapped[Optional["Company"]] = relationship(
        back_populates="document_chunks"
    )


# ============================================================
# 5. MarketEvent
# ============================================================
class MarketEvent(Base):
    __tablename__ = "market_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    source_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("raw_documents.id"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    event_subtype: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_title: Mapped[str] = mapped_column(Text, nullable=False)
    event_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    impact_label: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    impact_score: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric, nullable=True
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Numeric, nullable=True
    )
    severity: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entities: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    metrics: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    is_material: Mapped[bool] = mapped_column(Boolean, default=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)
    duplicate_of: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    # Relationships
    company: Mapped[Optional["Company"]] = relationship(back_populates="market_events")
    source_document: Mapped[Optional["RawDocument"]] = relationship(
        back_populates="events"
    )
    citations: Mapped[list["EventCitation"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


# ============================================================
# 6. EventCitation
# ============================================================
class EventCitation(Base):
    __tablename__ = "event_citations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_events.id", ondelete="CASCADE"),
        nullable=True,
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("raw_documents.id"), nullable=True
    )
    chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("document_chunks.id"), nullable=True
    )
    citation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    # Relationships
    event: Mapped[Optional["MarketEvent"]] = relationship(back_populates="citations")
    document: Mapped[Optional["RawDocument"]] = relationship(
        back_populates="citations"
    )


# ============================================================
# 7. User
# ============================================================
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auth_provider: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plan: Mapped[str] = mapped_column(Text, default="free")
    daily_chat_limit: Mapped[int] = mapped_column(Integer, default=20)
    daily_alert_limit: Mapped[int] = mapped_column(Integer, default=20)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    watchlists: Mapped[list["Watchlist"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user")


# ============================================================
# 8. Watchlist
# ============================================================
class Watchlist(Base):
    __tablename__ = "watchlists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="watchlists")
    companies: Mapped[list["WatchlistCompany"]] = relationship(
        back_populates="watchlist", cascade="all, delete-orphan"
    )


# ============================================================
# 9. WatchlistCompany
# ============================================================
class WatchlistCompany(Base):
    __tablename__ = "watchlist_companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    watchlist_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("watchlists.id", ondelete="CASCADE"),
        nullable=True,
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    alert_threshold: Mapped[str] = mapped_column(Text, default="medium")
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    __table_args__ = (UniqueConstraint("watchlist_id", "company_id"),)

    # Relationships
    watchlist: Mapped[Optional["Watchlist"]] = relationship(
        back_populates="companies"
    )


# ============================================================
# 10. ChatSession
# ============================================================
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    session_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(Text, default="general_market")
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


# ============================================================
# 11. ChatMessage
# ============================================================
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    model_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cost_estimate: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    # Relationships
    session: Mapped[Optional["ChatSession"]] = relationship(back_populates="messages")


# ============================================================
# 12. LLMApiKey (metadata only — keys encrypted at rest)
# ============================================================
class LLMApiKey(Base):
    __tablename__ = "llm_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    key_alias: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    daily_token_limit: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )
    used_tokens_today: Mapped[int] = mapped_column(BigInteger, default=0)
    rpm_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tpm_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    # Relationships
    usage_records: Mapped[list["ApiKeyUsage"]] = relationship(
        back_populates="api_key"
    )


# ============================================================
# 13. ApiKeyUsage
# ============================================================
class ApiKeyUsage(Base):
    __tablename__ = "api_key_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    api_key_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("llm_api_keys.id"), nullable=True
    )
    request_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    provider: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost_estimate: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    # Relationships
    api_key: Mapped[Optional["LLMApiKey"]] = relationship(
        back_populates="usage_records"
    )


# ============================================================
# 14. AuditLog (append-only with hash chaining)
# ============================================================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_type: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    current_hash: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )


# ============================================================
# 15. EvalRun
# ============================================================
class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    eval_type: Mapped[str] = mapped_column(Text, nullable=False)
    dataset_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rag_pipeline_version: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    score: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    report: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )


# ============================================================
# 16. SystemHealth
# ============================================================
class SystemHealth(Base):
    __tablename__ = "system_health"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    service_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_rate: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    queue_lag: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, default=dict
    )
    checked_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )


# ============================================================
# 17. StockSignalScore
# ============================================================
class StockSignalScore(Base):
    __tablename__ = "stock_signal_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    score_date: Mapped[date] = mapped_column(Date, nullable=False)
    bullish_score: Mapped[float] = mapped_column(Numeric, default=0)
    bearish_score: Mapped[float] = mapped_column(Numeric, default=0)
    quality_score: Mapped[float] = mapped_column(Numeric, default=0)
    momentum_score: Mapped[float] = mapped_column(Numeric, default=0)
    valuation_risk_score: Mapped[float] = mapped_column(Numeric, default=0)
    governance_risk_score: Mapped[float] = mapped_column(Numeric, default=0)
    news_sentiment_score: Mapped[float] = mapped_column(Numeric, default=0)
    event_strength_score: Mapped[float] = mapped_column(Numeric, default=0)
    confidence_score: Mapped[float] = mapped_column(Numeric, default=0)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    top_positive_factors: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list
    )
    top_negative_factors: Mapped[Optional[list]] = mapped_column(
        JSONB, default=list
    )
    source_event_ids: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    __table_args__ = (UniqueConstraint("company_id", "score_date"),)

    # Relationships
    company: Mapped[Optional["Company"]] = relationship(
        back_populates="signal_scores"
    )


# ============================================================
# 18. StockThesis
# ============================================================
class StockThesis(Base):
    __tablename__ = "stock_theses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    thesis_type: Mapped[str] = mapped_column(Text, nullable=False)
    thesis_title: Mapped[str] = mapped_column(Text, nullable=False)
    thesis_summary: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_points: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    risks: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    counterpoints: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    citations: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Numeric, nullable=True
    )
    generated_by_model: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )

    # Relationships
    company: Mapped[Optional["Company"]] = relationship(back_populates="theses")


# ============================================================
# 19. SemanticCache
# ============================================================
class SemanticCache(Base):
    __tablename__ = "semantic_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    normalized_query: Mapped[str] = mapped_column(Text, nullable=False)
    query_embedding = mapped_column(Vector(384), nullable=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[Optional[list]] = mapped_column(JSONB, default=list)
    mode: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True
    )
    fresh_until: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), server_default=func.now()
    )
