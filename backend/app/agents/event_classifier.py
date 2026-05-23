"""
Bharat Market Intelligence Agent — Event Classification Agent

Classifies incoming documents into structured market events.
Uses a multi-label classification approach:
1. Rule-based fast path for common patterns
2. LLM-powered classification for ambiguous cases

Event types: earnings, guidance, deal_win, rating_change, insider_trade,
governance_concern, regulatory_action, management_update, dividend,
buyback, fundraise, restructuring, production_update, product_launch
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Company, MarketEvent, RawDocument
from app.utils.helpers import truncate_text, utc_now

logger = logging.getLogger(__name__)


# ============================================================
# Rule-Based Classification Patterns
# ============================================================
# Each rule: (event_type, event_subtype, impact_label, severity, patterns)

CLASSIFICATION_RULES: list[tuple[str, Optional[str], str, str, list[str]]] = [
    # Earnings & Results
    ("earnings_commentary", "quarterly_results", "neutral", "high", [
        r"quarterly\s+results?", r"Q[1-4]\s+(FY|results?)", r"financial\s+results?",
        r"profit\s+(after|before)\s+tax", r"revenue\s+(from\s+operations|growth)",
        r"board\s+meeting\s+outcome.*results?", r"standalone.*consolidated.*results?",
    ]),

    # Guidance / Outlook
    ("guidance_revision", "guidance", "neutral", "high", [
        r"guidance\s+(revision|update)", r"outlook\s+(revised|updated|raised|lowered)",
        r"revenue\s+guidance", r"growth\s+guidance", r"margin\s+guidance",
    ]),

    # Deal Wins
    ("deal_win", "contract", "positive", "high", [
        r"(large\s+)?deal\s+win", r"order\s+(win|received|secured|bagged)",
        r"contract\s+(awarded|secured|received)", r"TCV\s+\$",
        r"mandate\s+(received|won)", r"new\s+engagement",
    ]),

    # Rating Changes
    ("rating_change", "upgrade", "positive", "high", [
        r"rating\s+upgrade", r"outlook\s+upgraded?\s+to\s+positive",
        r"credit\s+rating.*upgrade", r"rating.*revised\s+upward",
    ]),
    ("rating_change", "downgrade", "negative", "high", [
        r"rating\s+downgrade", r"outlook\s+downgraded?\s+to\s+negative",
        r"credit\s+rating.*downgrade", r"rating.*revised\s+downward",
        r"outlook.*negative", r"watch.*negative",
    ]),

    # Insider Trading / SAST
    ("insider_trade", "sast", "neutral", "medium", [
        r"insider\s+trading", r"SAST\s+regulation", r"substantial\s+acquisition",
        r"promoter.*(?:increase|decrease|sale|purchase).*holding",
        r"change\s+in\s+shareholding",
    ]),

    # Governance Concerns
    ("governance_concern", "regulatory_scrutiny", "negative", "high", [
        r"governance\s+concern", r"regulatory\s+scrutiny", r"SEBI\s+(order|notice|penalty)",
        r"fraud\s+allegation", r"whistle.?blower", r"related.?party\s+transaction",
        r"audit\s+qualification", r"forensic\s+audit", r"corporate\s+governance",
    ]),

    # Regulatory Actions
    ("regulatory_action", "fda", "negative", "high", [
        r"form\s+483", r"USFDA\s+observation", r"FDA\s+warning\s+letter",
        r"import\s+alert", r"GMP\s+non.?compliance",
    ]),
    ("regulatory_action", "penalty", "negative", "medium", [
        r"penalty\s+imposed", r"fine\s+levied", r"regulatory\s+action",
        r"show\s+cause\s+notice", r"RBI\s+penalty", r"SEBI\s+penalty",
    ]),

    # Management Changes
    ("management_update", "appointment", "neutral", "medium", [
        r"(CEO|CFO|MD|Chairman)\s+(appointed|resigned|stepped\s+down)",
        r"appointment\s+of", r"resignation\s+of", r"change\s+in\s+(key\s+)?managerial",
        r"new\s+(CEO|CFO|MD|Chairman|director)", r"board\s+re.?constitution",
    ]),

    # Dividends
    ("dividend", "interim", "positive", "low", [
        r"interim\s+dividend", r"special\s+dividend", r"final\s+dividend",
        r"dividend\s+declared", r"record\s+date.*dividend",
    ]),

    # Buyback
    ("buyback", None, "positive", "medium", [
        r"share\s+buyback", r"buyback\s+of\s+shares", r"buy.?back\s+offer",
        r"tender\s+offer.*buyback",
    ]),

    # Fundraise
    ("fundraise", "qip", "neutral", "medium", [
        r"QIP\s+(issue|allotment|raised)", r"qualified\s+institutions?\s+placement",
        r"rights\s+issue", r"preferential\s+allotment", r"fund\s+raise",
        r"bond\s+issuance", r"NCD\s+issue", r"equity\s+raise",
    ]),

    # Restructuring
    ("restructuring", None, "neutral", "high", [
        r"(merger|acquisition|demerger|amalgamation)", r"scheme\s+of\s+arrangement",
        r"spin.?off", r"slump\s+sale", r"divestment", r"subsidiary.*formation",
        r"restructur", r"business\s+transfer",
    ]),

    # Production & Operations
    ("production_update", None, "neutral", "medium", [
        r"production\s+(update|data|shortfall|expansion|target)",
        r"plant\s+(capacity|expansion|commissioning|shutdown)",
        r"capacity\s+(expansion|addition|utilization)",
        r"COD\s+(achieved|declared)", r"commercial\s+production",
    ]),

    # Product Launch
    ("product_launch", None, "positive", "medium", [
        r"product\s+launch", r"new\s+product", r"ANDA\s+approval",
        r"patent\s+(granted|approved)", r"drug\s+approval",
        r"new\s+model\s+launch", r"(EV|electric\s+vehicle)\s+launch",
    ]),

    # Board Meeting
    ("board_meeting", None, "neutral", "low", [
        r"board\s+meeting\s+(scheduled|notice|to\s+consider)",
        r"intimation\s+of\s+board\s+meeting",
    ]),
]


def classify_document(
    title: str,
    text: str,
    metadata: Optional[dict] = None,
) -> dict[str, Any]:
    """
    Classify a document into a structured market event using rule-based patterns.

    Args:
        title: Document title/headline
        text: Full document text
        metadata: Optional metadata from source

    Returns:
        Classification result dict
    """
    combined = f"{title} {text}".lower()
    metadata = metadata or {}

    best_match: Optional[dict] = None
    best_score = 0

    for event_type, event_subtype, impact, severity, patterns in CLASSIFICATION_RULES:
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            score += len(matches)

        if score > best_score:
            best_score = score
            best_match = {
                "event_type": event_type,
                "event_subtype": event_subtype,
                "impact_label": impact,
                "severity": severity,
                "confidence_score": min(0.95, 0.5 + score * 0.1),
            }

    if not best_match:
        best_match = {
            "event_type": "general_update",
            "event_subtype": None,
            "impact_label": "neutral",
            "severity": "low",
            "confidence_score": 0.3,
        }

    # Sentiment heuristics
    sentiment = _compute_sentiment(combined)
    best_match["sentiment_score"] = sentiment

    # Adjust impact based on sentiment if rule gave neutral
    if best_match["impact_label"] == "neutral":
        if sentiment > 0.3:
            best_match["impact_label"] = "positive"
        elif sentiment < -0.3:
            best_match["impact_label"] = "negative"

    return best_match


def _compute_sentiment(text: str) -> float:
    """
    Simple keyword-based sentiment scoring.
    Returns value between -1.0 (negative) and 1.0 (positive).
    """
    positive_words = [
        "growth", "strong", "record", "improvement", "upgrade", "positive",
        "profit", "beat", "exceeded", "outperform", "surge", "rally",
        "robust", "expansion", "optimistic", "upside", "bullish",
        "accelerat", "momentum", "healthy", "resilient", "improve",
    ]
    negative_words = [
        "decline", "loss", "weak", "concern", "downgrade", "negative",
        "miss", "below", "underperform", "fall", "drop", "slump",
        "warning", "risk", "penalty", "fraud", "scrutiny", "downturn",
        "decelerat", "pressure", "headwind", "cautious", "deteriorat",
    ]

    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)

    total = pos_count + neg_count
    if total == 0:
        return 0.0

    return round((pos_count - neg_count) / total, 3)


async def classify_and_create_event(
    document_id: UUID,
    db: AsyncSession,
) -> Optional[UUID]:
    """
    Classify a raw document and create a MarketEvent from it.

    Args:
        document_id: UUID of the raw document to classify
        db: Database session

    Returns:
        MarketEvent UUID if created, None otherwise
    """
    # Fetch document
    result = await db.execute(
        select(RawDocument).where(RawDocument.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        logger.error("Document not found: %s", document_id)
        return None

    title = doc.title or ""
    text = doc.raw_text or ""

    if not title and not text:
        return None

    # Classify
    classification = classify_document(title, text, doc.metadata_json)

    # Create event
    event = MarketEvent(
        company_id=doc.company_id,
        source_document_id=doc.id,
        event_type=classification["event_type"],
        event_subtype=classification.get("event_subtype"),
        event_title=truncate_text(title, 200) or "Untitled Event",
        event_summary=truncate_text(text, 500),
        impact_label=classification["impact_label"],
        impact_score=classification.get("confidence_score", 0.5),
        confidence_score=classification.get("confidence_score", 0.5),
        sentiment_score=classification.get("sentiment_score", 0.0),
        severity=classification.get("severity", "low"),
        event_time=doc.published_at.replace(tzinfo=None) if doc.published_at else None,
        source_url=doc.url,
        is_material=classification.get("severity") in ("high", "critical"),
    )
    db.add(event)
    await db.flush()

    logger.info(
        "Created event: [%s] %s → %s (%.0f%% conf)",
        classification["event_type"],
        title[:50],
        classification["impact_label"],
        classification.get("confidence_score", 0) * 100,
    )

    return event.id
