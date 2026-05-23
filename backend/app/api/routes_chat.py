"""
Bharat Market Intelligence Agent — Chat Routes

Full 8-layer chat routing pipeline:
1. Compliance guardrail
2. Query normalization
3. Exact cache lookup
4. Semantic cache lookup
5. Company-scoped SQL answer
6. RAG + LLM answer
7. LLM-only fallback
8. Source-only fallback
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatMessage, ChatSession, Company, SemanticCache
from app.db.schemas import ChatRequest, ChatResponse, CitationItem
from app.db.session import get_db
from app.utils.helpers import normalize_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# ============================================================
# Compliance Guardrails
# ============================================================
UNSAFE_PATTERNS = [
    "which stock to buy",
    "stocks to buy",
    "guaranteed",
    "multibagger",
    "sure shot",
    "invest my salary",
    "stock should i short",
    "insider information",
    "insider tip",
    "intraday tip",
    "buy call",
    "sell call",
    "stock tips",
    "penny stock",
    "how to get rich",
    "pump and dump",
    "target price",
    "what to invest in",
]

SAFE_REFUSAL = (
    "I can summarize public signals, risks, and recent events for research purposes, "
    "but I cannot provide personalized investment advice, guaranteed recommendations, "
    "or buy/sell/short calls. Please consult a SEBI-registered investment adviser "
    "for personalized guidance."
)

DISCLAIMER = (
    "This is informational and not investment advice. "
    "Please verify independently and consult a SEBI-registered adviser."
)


def _check_compliance(message: str) -> Optional[str]:
    """Check if query contains unsafe financial advice patterns."""
    lower = message.lower()
    for pattern in UNSAFE_PATTERNS:
        if pattern in lower:
            return SAFE_REFUSAL
    return None


# ============================================================
# Chat Endpoint — Full Pipeline
# ============================================================
@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Chat with the market intelligence system.

    Uses an 8-layer routing strategy for optimal quality/speed/cost:
    1. Compliance guardrail — block unsafe queries
    2. Query normalization
    3. Exact cache hit
    4. Semantic cache (vector similarity)
    5. Company SQL lookup (for factual queries)
    6. RAG + LLM (primary answer path)
    7. LLM-only (when RAG context is empty)
    8. Source-only (when all LLMs fail)
    """
    start_time = time.time()

    # ── Layer 1: Compliance Guardrail ────────────────────────
    refusal = _check_compliance(request.message)
    if refusal:
        return ChatResponse(
            answer=refusal,
            confidence="high",
            limitations="Query blocked by compliance guardrail.",
            disclaimer=DISCLAIMER,
            model_used="compliance_filter",
            latency_ms=int((time.time() - start_time) * 1000),
        )

    # ── Layer 2: Normalize Query ─────────────────────────────
    normalized = normalize_query(request.message)

    # ── Layer 3: Exact Cache ─────────────────────────────────
    cached_response = await _check_exact_cache(normalized, db)
    if cached_response:
        cached_response["latency_ms"] = int((time.time() - start_time) * 1000)
        cached_response["cached"] = True
        return ChatResponse(**cached_response)

    # ── Layer 5: Company Factual Query ───────────────────────
    if request.company_symbol or request.mode == "company_deep_dive":
        company_answer = await _try_company_lookup(
            request.message, request.company_symbol, db
        )
        if company_answer:
            latency = int((time.time() - start_time) * 1000)
            return ChatResponse(
                answer=company_answer["answer"],
                citations=[CitationItem(**c) for c in company_answer.get("citations", [])],
                confidence="medium",
                disclaimer=DISCLAIMER,
                model_used="sql_lookup",
                latency_ms=latency,
                session_id=request.session_id,
            )

    # ── Layer 6: RAG + LLM ──────────────────────────────────
    try:
        from app.services.llm_router import build_chat_messages, route_llm_request
        from app.services.rag_service import get_context_for_query

        context, citations = await get_context_for_query(
            query=request.message,
            db=db,
            company_symbol=request.company_symbol,
        )

        if context:
            # Have context → RAG answer
            messages = build_chat_messages(
                user_query=request.message,
                context=context,
            )
            llm_result = await route_llm_request(messages=messages)
            latency = int((time.time() - start_time) * 1000)

            citation_items = [
                CitationItem(
                    source=c.get("source", "Unknown"),
                    published_at=c.get("published_at"),
                    snippet=c.get("snippet", ""),
                    url=c.get("url"),
                )
                for c in citations
            ]

            # Store in session if provided
            await _store_chat_message(
                session_id=request.session_id,
                user_message=request.message,
                assistant_message=llm_result["answer"],
                model_used=llm_result.get("model", ""),
                latency_ms=latency,
                db=db,
            )

            return ChatResponse(
                answer=llm_result["answer"],
                citations=citation_items,
                confidence="high" if citations else "medium",
                disclaimer=DISCLAIMER,
                model_used=llm_result.get("model", "unknown"),
                latency_ms=latency,
                session_id=request.session_id,
            )

        # ── Layer 7: LLM-only (no context) ──────────────────
        messages = build_chat_messages(
            user_query=request.message,
            context="",
        )
        llm_result = await route_llm_request(messages=messages)
        latency = int((time.time() - start_time) * 1000)

        return ChatResponse(
            answer=llm_result["answer"],
            confidence="low",
            limitations="No source documents found. Response is based on general knowledge.",
            disclaimer=DISCLAIMER,
            model_used=llm_result.get("model", "unknown"),
            latency_ms=latency,
            session_id=request.session_id,
        )

    except Exception as e:
        logger.error("Chat pipeline error: %s", str(e))

    # ── Layer 8: Source-Only Fallback ────────────────────────
    latency = int((time.time() - start_time) * 1000)
    return ChatResponse(
        answer=(
            "I'm currently unable to generate an AI response. "
            "However, you can explore the latest events on the Dashboard, "
            "or check the Bullish/Bearish watchlists for signal candidates. "
            "The system is designed to provide source-cited answers — "
            "please try again shortly."
        ),
        confidence="low",
        limitations="AI pipeline temporarily unavailable. Showing fallback response.",
        disclaimer=DISCLAIMER,
        model_used="source_only_fallback",
        latency_ms=latency,
        session_id=request.session_id,
    )


# ============================================================
# Helper Functions
# ============================================================
async def _check_exact_cache(
    normalized_query: str,
    db: AsyncSession,
) -> Optional[dict[str, Any]]:
    """Check for exact cache hit."""
    try:
        result = await db.execute(
            select(SemanticCache).where(
                SemanticCache.normalized_query == normalized_query
            )
        )
        cached = result.scalar_one_or_none()
        if cached:
            # Update hit count
            cached.hit_count += 1
            await db.flush()

            # Check freshness
            if cached.fresh_until and cached.fresh_until < datetime.now(timezone.utc).replace(tzinfo=None):
                return None  # Cache entry expired

            return {
                "answer": cached.answer,
                "citations": [
                    CitationItem(**c) for c in (cached.citations or [])
                ],
                "confidence": "high",
                "disclaimer": DISCLAIMER,
                "model_used": "exact_cache",
            }
    except Exception as e:
        logger.debug("Cache check failed: %s", str(e))

    return None


async def _try_company_lookup(
    query: str,
    company_symbol: Optional[str],
    db: AsyncSession,
) -> Optional[dict[str, Any]]:
    """Try to answer with direct company data lookup."""
    if not company_symbol:
        return None

    try:
        result = await db.execute(
            select(Company).where(
                (Company.symbol == company_symbol.upper())
                | (Company.nse_symbol == company_symbol.upper())
            )
        )
        company = result.scalar_one_or_none()
        if not company:
            return None

        # Build factual answer from company data
        answer = (
            f"**{company.company_name}** ({company.symbol})\n\n"
            f"• **Exchange:** {company.exchange}\n"
            f"• **Sector:** {company.sector or 'N/A'}\n"
            f"• **Industry:** {company.industry or 'N/A'}\n"
        )
        if company.isin:
            answer += f"• **ISIN:** {company.isin}\n"
        if company.bse_code:
            answer += f"• **BSE Code:** {company.bse_code}\n"
        if company.market_cap:
            answer += f"• **Market Cap:** ₹{company.market_cap:,.0f} Cr\n"
        if company.website:
            answer += f"• **Website:** {company.website}\n"

        answer += (
            "\nFor detailed analysis, event history, and signal scores, "
            "ask a more specific question like 'What events happened with "
            f"{company.symbol} this week?' or 'Show me the thesis for {company.symbol}'."
        )

        return {
            "answer": answer,
            "citations": [{
                "source": "Company Database",
                "snippet": f"{company.company_name} — {company.sector}",
                "url": company.website,
            }],
        }
    except Exception as e:
        logger.debug("Company lookup failed: %s", str(e))
        return None


async def _store_chat_message(
    session_id: Optional[UUID],
    user_message: str,
    assistant_message: str,
    model_used: str,
    latency_ms: int,
    db: AsyncSession,
) -> None:
    """Store chat messages in the database for history."""
    if not session_id:
        return

    try:
        # Check if session exists
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            # Create new session
            session = ChatSession(id=session_id, mode="general_market")
            db.add(session)
            await db.flush()

        # Store user message
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=user_message,
        )
        db.add(user_msg)

        # Store assistant message
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=assistant_message,
            model_used=model_used,
            latency_ms=latency_ms,
        )
        db.add(assistant_msg)

        await db.flush()
    except Exception as e:
        logger.debug("Failed to store chat message: %s", str(e))
