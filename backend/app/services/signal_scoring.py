"""
Bharat Market Intelligence Agent — Signal Scoring Service

Computes bullish/bearish signal scores for companies based on:
1. Recent event sentiment aggregation
2. Event type weighting
3. Event recency decay
4. Material event boosting
5. Confidence-weighted scoring

Stores results in stock_signal_scores table.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, MarketEvent, StockSignalScore
from app.utils.helpers import utc_now

logger = logging.getLogger(__name__)

# Event type weights for signal scoring
EVENT_WEIGHTS = {
    "earnings_commentary": 2.0,
    "guidance_revision": 2.5,
    "deal_win": 1.8,
    "rating_change": 2.2,
    "insider_trade": 1.5,
    "governance_concern": 2.5,
    "regulatory_action": 2.3,
    "management_update": 1.3,
    "dividend": 1.0,
    "buyback": 1.5,
    "fundraise": 1.2,
    "restructuring": 2.0,
    "production_update": 1.3,
    "product_launch": 1.5,
    "board_meeting": 0.5,
    "general_update": 0.3,
}

# Severity multipliers
SEVERITY_MULTIPLIERS = {
    "critical": 2.0,
    "high": 1.5,
    "medium": 1.0,
    "low": 0.5,
}


def _recency_decay(hours_ago: float, half_life_hours: float = 72.0) -> float:
    """Exponential decay based on event age. Half-life = 72 hours by default."""
    return math.exp(-0.693 * hours_ago / half_life_hours)


async def compute_company_signal(
    company_id: UUID,
    db: AsyncSession,
    lookback_days: int = 30,
) -> dict[str, Any]:
    """
    Compute bullish/bearish signal score for a single company.

    Uses event sentiment, type weights, recency decay, and confidence.
    """
    now = utc_now().replace(tzinfo=None)
    cutoff = now - timedelta(days=lookback_days)

    # Fetch recent events
    result = await db.execute(
        select(MarketEvent).where(
            and_(
                MarketEvent.company_id == company_id,
                MarketEvent.detected_at >= cutoff,
            )
        ).order_by(MarketEvent.detected_at.desc())
    )
    events = result.scalars().all()

    if not events:
        return {
            "company_id": str(company_id),
            "bullish_score": 5.0,
            "bearish_score": 5.0,
            "net_score": 0.0,
            "event_count": 0,
            "top_positive_factors": [],
            "top_negative_factors": [],
        }

    positive_signals = []
    negative_signals = []
    total_bullish = 0.0
    total_bearish = 0.0
    total_weight = 0.0

    for event in events:
        # Calculate weights
        event_weight = EVENT_WEIGHTS.get(event.event_type or "", 0.5)
        severity_mult = SEVERITY_MULTIPLIERS.get(event.severity or "medium", 1.0)

        # Recency decay
        if event.detected_at:
            dt = event.detected_at.replace(tzinfo=None) if event.detected_at.tzinfo else event.detected_at
            hours_ago = (now - dt).total_seconds() / 3600
        else:
            hours_ago = 24.0
        decay = _recency_decay(hours_ago)

        # Material boost
        material_boost = 1.5 if event.is_material else 1.0

        # Confidence weight
        confidence = float(event.confidence_score) if event.confidence_score is not None else 0.5

        # Combined weight
        combined_weight = event_weight * severity_mult * decay * material_boost * confidence

        # Apply to bullish/bearish based on impact
        sentiment = float(event.sentiment_score) if event.sentiment_score is not None else 0.0
        impact = event.impact_label or "neutral"

        if impact == "positive" or sentiment > 0.2:
            total_bullish += combined_weight * max(0.5, 0.5 + sentiment)
            positive_signals.append({
                "factor": event.event_title or event.event_type,
                "weight": round(combined_weight, 2),
                "type": event.event_type,
            })
        elif impact == "negative" or sentiment < -0.2:
            total_bearish += combined_weight * max(0.5, 0.5 - sentiment)
            negative_signals.append({
                "factor": event.event_title or event.event_type,
                "weight": round(combined_weight, 2),
                "type": event.event_type,
            })
        else:
            # Neutral events contribute slightly to both
            total_bullish += combined_weight * 0.2
            total_bearish += combined_weight * 0.2

        total_weight += combined_weight

    # Normalize to 0-10 scale
    if total_weight > 0:
        raw_bullish = total_bullish / total_weight * 10
        raw_bearish = total_bearish / total_weight * 10
    else:
        raw_bullish = 5.0
        raw_bearish = 5.0

    # Clamp to [1, 10]
    bullish_score = round(max(1.0, min(10.0, raw_bullish)), 1)
    bearish_score = round(max(1.0, min(10.0, raw_bearish)), 1)
    net_score = round(bullish_score - bearish_score, 1)

    # Sort factors by weight
    positive_signals.sort(key=lambda x: x["weight"], reverse=True)
    negative_signals.sort(key=lambda x: x["weight"], reverse=True)

    return {
        "company_id": str(company_id),
        "bullish_score": bullish_score,
        "bearish_score": bearish_score,
        "net_score": net_score,
        "event_count": len(events),
        "top_positive_factors": [s["factor"] for s in positive_signals[:5]],
        "top_negative_factors": [s["factor"] for s in negative_signals[:5]],
        "scoring_window_days": lookback_days,
    }


async def rank_all_signals(
    db: AsyncSession,
    lookback_days: int = 30,
    min_events: int = 1,
) -> dict[str, Any]:
    """
    Compute signal scores for all active companies with recent events.
    Stores results in stock_signal_scores table.
    """
    now = utc_now().replace(tzinfo=None)
    cutoff = now - timedelta(days=lookback_days)

    # Find companies with recent events
    company_query = (
        select(MarketEvent.company_id)
        .where(
            and_(
                MarketEvent.company_id.is_not(None),
                MarketEvent.detected_at >= cutoff,
            )
        )
        .group_by(MarketEvent.company_id)
        .having(func.count(MarketEvent.id) >= min_events)
    )

    result = await db.execute(company_query)
    company_ids = [row[0] for row in result.all()]

    logger.info("Computing signals for %d companies", len(company_ids))

    all_scores = []
    for cid in company_ids:
        try:
            score = await compute_company_signal(cid, db, lookback_days)
            all_scores.append(score)

            # Fetch company info
            company_result = await db.execute(
                select(Company).where(Company.id == cid)
            )
            company = company_result.scalar_one_or_none()

            if company:
                # Upsert signal score
                existing = await db.execute(
                    select(StockSignalScore).where(
                        StockSignalScore.company_id == cid
                    )
                )
                signal = existing.scalar_one_or_none()

                if signal:
                    signal.bullish_score = score["bullish_score"]
                    signal.bearish_score = score["bearish_score"]
                    signal.top_positive_factors = score["top_positive_factors"]
                    signal.top_negative_factors = score["top_negative_factors"]
                    signal.score_date = now.date()
                else:
                    signal = StockSignalScore(
                        company_id=cid,
                        bullish_score=score["bullish_score"],
                        bearish_score=score["bearish_score"],
                        top_positive_factors=score["top_positive_factors"],
                        top_negative_factors=score["top_negative_factors"],
                        score_date=now.date(),
                    )
                    db.add(signal)

        except Exception as e:
            logger.error("Signal computation failed for %s: %s", cid, str(e))

    await db.commit()

    # Sort for top bullish/bearish
    bullish_sorted = sorted(all_scores, key=lambda x: x["bullish_score"], reverse=True)
    bearish_sorted = sorted(all_scores, key=lambda x: x["bearish_score"], reverse=True)

    return {
        "total_companies_scored": len(all_scores),
        "scoring_window_days": lookback_days,
        "computed_at": now.isoformat(),
        "top_bullish": bullish_sorted[:20],
        "top_bearish": bearish_sorted[:20],
    }
