"""
Bharat Market Intelligence Agent — NSE Corporate Filings Scraper

LEVEL 1 SOURCE — Fastest possible data.
Fetches directly from NSE India's corporate announcements API.
This is the legally mandated origin point for all market-moving news.
Companies MUST notify the exchange before anyone else (SEBI regulation).

Endpoints used:
- Corporate announcements (board meeting outcomes, SAST, etc.)
- Corporate actions (dividends, splits, bonus, rights)
- Board meetings scheduled

Legal: Public data from NSE's official website. No login required.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.utils.helpers import clean_text, compute_content_hash

logger = logging.getLogger(__name__)

# NSE requires specific headers to respond — behaves like a browser
NSE_BASE = "https://www.nseindia.com"
NSE_API = "https://www.nseindia.com/api"

NSE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
    "X-Requested-With": "XMLHttpRequest",
}

REQUEST_TIMEOUT = 15.0

# Speed tier metadata
SOURCE_TIER = 1  # Level 1: Exchange source (0 second delay)
SOURCE_LATENCY_LABEL = "exchange_instant"


async def _get_nse_session() -> httpx.AsyncClient:
    """
    Create an authenticated NSE session.
    NSE requires a cookie from the main page before API calls work.
    """
    client = httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
        headers=NSE_HEADERS,
    )
    # Hit the main page to get session cookies
    try:
        await client.get(NSE_BASE)
    except Exception:
        pass  # Cookie may still be set even on partial failure
    return client


async def fetch_nse_corporate_announcements(
    index: str = "equities",
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Fetch corporate announcements from NSE India.

    This is the FASTEST source — filings appear here before
    any news article, Bloomberg terminal, or aggregator.

    Args:
        index: 'equities', 'sme', 'debt'
        from_date: DD-MM-YYYY format
        to_date: DD-MM-YYYY format

    Returns:
        List of normalized announcement dicts
    """
    now = datetime.now()
    if not from_date:
        from_date = now.strftime("%d-%m-%Y")
    if not to_date:
        to_date = now.strftime("%d-%m-%Y")

    url = f"{NSE_API}/corporate-announcements"
    params = {
        "index": index,
        "from_date": from_date,
        "to_date": to_date,
    }

    announcements = []

    try:
        client = await _get_nse_session()
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            items = data if isinstance(data, list) else data.get("data", data.get("items", []))

            for item in items:
                parsed = _parse_nse_announcement(item)
                if parsed:
                    announcements.append(parsed)

            logger.info(
                "NSE Level-1: fetched %d corporate announcements (%s to %s)",
                len(announcements), from_date, to_date,
            )
        finally:
            await client.aclose()

    except httpx.HTTPStatusError as e:
        logger.error("NSE API HTTP error: %d", e.response.status_code)
    except httpx.TimeoutException:
        logger.error("NSE API timeout — exchange may be rate-limiting")
    except Exception as e:
        logger.error("NSE API failed: %s", str(e))

    return announcements


def _parse_nse_announcement(raw: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Parse a single NSE corporate announcement."""
    try:
        subject = clean_text(raw.get("desc", "") or raw.get("subject", "") or "")
        if not subject:
            return None

        company_name = clean_text(raw.get("companyName", "") or raw.get("company_name", "") or "")
        symbol = (raw.get("symbol", "") or "").strip().upper()
        an_dt = raw.get("an_dt", "") or raw.get("date", "")
        category = raw.get("attchmntFile", "") or ""  # Attachment filename
        broadcast_dt = raw.get("brdcst_dt", "")       # Broadcast datetime

        # Parse timestamp — NSE uses "DD-Mon-YYYY HH:MM:SS" format
        published_at = None
        for dt_field in [broadcast_dt, an_dt]:
            if dt_field:
                try:
                    published_at = datetime.strptime(dt_field, "%d-%b-%Y %H:%M:%S")
                    published_at = published_at.replace(tzinfo=timezone.utc)
                    break
                except (ValueError, TypeError):
                    try:
                        published_at = datetime.fromisoformat(dt_field.replace("Z", "+00:00"))
                        break
                    except (ValueError, TypeError):
                        pass

        # Extract filing category from NSE metadata
        filing_category = raw.get("categoryOfAnnouncement", "") or raw.get("category", "")

        # Attachment URL
        attachment = raw.get("attchmntFile", "")
        attachment_url = None
        if attachment:
            attachment_url = f"https://nsearchives.nseindia.com/corporate/Announcement_{attachment}"

        # Content hash
        hash_content = f"NSE|{symbol}|{subject}|{broadcast_dt or an_dt}"
        content_hash = compute_content_hash(hash_content)

        # Real-time sentiment classification
        sentiment = _classify_sentiment_fast(subject, filing_category)

        return {
            "source": "nse_exchange",
            "source_tier": SOURCE_TIER,
            "source_latency": SOURCE_LATENCY_LABEL,
            "source_url": f"https://www.nseindia.com/companies-listing/corporate-filings-announcements",
            "company_name": company_name,
            "nse_symbol": symbol,
            "document_type": "exchange_filing",
            "title": subject,
            "raw_text": subject,
            "published_at": published_at,
            "ingested_at": datetime.now(timezone.utc),
            "content_hash": content_hash,
            "attachment_url": attachment_url,
            "sentiment_label": sentiment["label"],
            "sentiment_score": sentiment["score"],
            "metadata": {
                "exchange": "NSE",
                "symbol": symbol,
                "filing_category": filing_category,
                "attachment": attachment,
                "source_tier": SOURCE_TIER,
                "broadcast_dt": broadcast_dt,
            },
        }
    except Exception as e:
        logger.error("Failed to parse NSE announcement: %s", str(e))
        return None


async def fetch_nse_board_meetings() -> list[dict[str, Any]]:
    """
    Fetch upcoming board meeting dates from NSE.
    These are leading indicators — markets move on anticipation.
    """
    url = f"{NSE_API}/corporate-board-meetings"
    params = {"index": "equities"}

    meetings = []
    try:
        client = await _get_nse_session()
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            items = data if isinstance(data, list) else data.get("data", [])
            for item in items:
                purpose = clean_text(item.get("bm_purpose", "") or "")
                symbol = (item.get("symbol", "") or "").strip().upper()
                meeting_date = item.get("bm_date", "")

                if purpose and symbol:
                    hash_content = f"NSE_BM|{symbol}|{purpose}|{meeting_date}"
                    sentiment = _classify_sentiment_fast(purpose, "board_meeting")

                    meetings.append({
                        "source": "nse_exchange",
                        "source_tier": SOURCE_TIER,
                        "source_latency": SOURCE_LATENCY_LABEL,
                        "source_url": "https://www.nseindia.com/companies-listing/corporate-filings-board-meetings",
                        "nse_symbol": symbol,
                        "company_name": item.get("companyName", ""),
                        "document_type": "board_meeting_notice",
                        "title": f"[Board Meeting] {symbol}: {purpose}",
                        "raw_text": f"Board meeting for {symbol} on {meeting_date}. Purpose: {purpose}",
                        "published_at": datetime.now(timezone.utc),
                        "ingested_at": datetime.now(timezone.utc),
                        "content_hash": compute_content_hash(hash_content),
                        "sentiment_label": sentiment["label"],
                        "sentiment_score": sentiment["score"],
                        "metadata": {
                            "exchange": "NSE",
                            "symbol": symbol,
                            "meeting_date": meeting_date,
                            "purpose": purpose,
                            "source_tier": SOURCE_TIER,
                        },
                    })

            logger.info("NSE Level-1: fetched %d board meeting notices", len(meetings))
        finally:
            await client.aclose()

    except Exception as e:
        logger.error("NSE board meetings fetch failed: %s", str(e))

    return meetings


async def fetch_nse_corporate_actions() -> list[dict[str, Any]]:
    """
    Fetch corporate actions (dividends, splits, bonus, rights) from NSE.
    """
    url = f"{NSE_API}/corporates-corporateActions"
    params = {"index": "equities"}

    actions = []
    try:
        client = await _get_nse_session()
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            items = data if isinstance(data, list) else data.get("data", [])
            for item in items:
                symbol = (item.get("symbol", "") or "").strip().upper()
                subject = clean_text(item.get("subject", "") or "")
                ex_date = item.get("exDate", "")
                record_date = item.get("recordDate", "")

                if subject and symbol:
                    hash_content = f"NSE_CA|{symbol}|{subject}|{ex_date}"
                    sentiment = _classify_sentiment_fast(subject, "corporate_action")

                    actions.append({
                        "source": "nse_exchange",
                        "source_tier": SOURCE_TIER,
                        "source_latency": SOURCE_LATENCY_LABEL,
                        "source_url": "https://www.nseindia.com/companies-listing/corporate-filings-actions",
                        "nse_symbol": symbol,
                        "company_name": item.get("companyName", ""),
                        "document_type": "corporate_action",
                        "title": f"[Corp Action] {symbol}: {subject}",
                        "raw_text": f"{subject} — Ex-Date: {ex_date}, Record Date: {record_date}",
                        "published_at": datetime.now(timezone.utc),
                        "ingested_at": datetime.now(timezone.utc),
                        "content_hash": compute_content_hash(hash_content),
                        "sentiment_label": sentiment["label"],
                        "sentiment_score": sentiment["score"],
                        "metadata": {
                            "exchange": "NSE",
                            "symbol": symbol,
                            "ex_date": ex_date,
                            "record_date": record_date,
                            "source_tier": SOURCE_TIER,
                        },
                    })

            logger.info("NSE Level-1: fetched %d corporate actions", len(actions))
        finally:
            await client.aclose()

    except Exception as e:
        logger.error("NSE corporate actions fetch failed: %s", str(e))

    return actions


async def fetch_all_nse_filings() -> list[dict[str, Any]]:
    """
    Fetch ALL NSE Level-1 data:
    1. Corporate announcements (board meeting outcomes, SAST, etc.)
    2. Board meeting notices (upcoming — leading indicators)
    3. Corporate actions (dividends, splits, bonus)

    Returns deduplicated, sentiment-tagged filings.
    """
    all_filings = []
    seen_hashes: set[str] = set()

    # 1. Corporate announcements (highest priority)
    announcements = await fetch_nse_corporate_announcements()
    for a in announcements:
        if a["content_hash"] not in seen_hashes:
            seen_hashes.add(a["content_hash"])
            all_filings.append(a)

    # 2. Board meetings
    meetings = await fetch_nse_board_meetings()
    for m in meetings:
        if m["content_hash"] not in seen_hashes:
            seen_hashes.add(m["content_hash"])
            all_filings.append(m)

    # 3. Corporate actions
    actions = await fetch_nse_corporate_actions()
    for a in actions:
        if a["content_hash"] not in seen_hashes:
            seen_hashes.add(a["content_hash"])
            all_filings.append(a)

    logger.info(
        "NSE Level-1 TOTAL: %d filings (%d announcements, %d meetings, %d actions)",
        len(all_filings), len(announcements), len(meetings), len(actions),
    )

    return all_filings


# ============================================================
# Real-Time Sentiment Classification
# ============================================================
# These patterns run at ingestion time — instant bullish/bearish tagging
# before any LLM call, so the frontend shows signals immediately.

BULLISH_PATTERNS = [
    # Earnings positive
    r"(?:net\s+)?profit\s+(?:up|rise|increas|grew|surge|jump|record)",
    r"revenue\s+(?:growth|up|increase|surge|jump|beat)",
    r"strong\s+(?:results?|performance|growth|quarter)",
    r"beat\s+(?:estimate|expectation|consensus)",
    r"margin\s+(?:expansion|improvement|improved)",
    r"guidance\s+(?:raised|upgraded|increased)",
    # Deals & orders
    r"(?:large\s+)?deal\s+(?:win|won|signed|secured|awarded)",
    r"order\s+(?:win|won|received|bagged|secured)",
    r"contract\s+(?:awarded|signed|secured|received)",
    # Positive corporate actions
    r"(?:interim|final|special)\s+dividend",
    r"buy\s*back\s+(?:of\s+shares?|offer|approved)",
    r"rating\s+(?:upgrade|affirmed?\s+with\s+positive)",
    r"outlook\s+(?:positive|stable|revised\s+to\s+positive)",
    # Growth signals
    r"(?:capacity|production)\s+expansion",
    r"new\s+(?:product|plant|facility|launch)",
    r"(?:ANDA|drug|patent)\s+approv",
    r"strategic\s+(?:partnership|alliance|collaboration)",
    r"acquisition\s+(?:of|completed|announced)",
]

BEARISH_PATTERNS = [
    # Earnings negative
    r"(?:net\s+)?(?:profit|revenue)\s+(?:down|decline|fell|drop|miss|decreas|weak|plunge)",
    r"(?:net\s+)?loss\s+(?:of|reported|widened|deepened)",
    r"miss(?:ed)?\s+(?:estimate|expectation|consensus|guidance)",
    r"margin\s+(?:compression|contraction|decline|pressure)",
    r"guidance\s+(?:cut|lowered|reduced|withdrawn|revised\s+down)",
    # Governance & regulatory
    r"(?:SEBI|RBI|NCLT|SAT)\s+(?:penalty|fine|order|notice|ban|warning)",
    r"(?:form\s+483|warning\s+letter|import\s+alert|FDA\s+observation)",
    r"(?:fraud|scam|misappropriation|embezzlement)\s+(?:alleged|detected|found)",
    r"(?:forensic|statutory)\s+audit\s+(?:ordered|initiated|reveal)",
    r"whistle\s*blow",
    r"(?:related\s+party|RPT)\s+(?:transaction|concern)",
    r"governance\s+(?:concern|issue|failure|lapse)",
    # Management issues
    r"(?:CEO|CFO|MD|Chairman|auditor)\s+(?:resign|step(?:ped)?\s+down|quit|exit|removal)",
    r"key\s+managerial\s+personnel.*(?:resign|change|exit)",
    # Financial stress
    r"(?:debt|NPA)\s+(?:default|restructur|slippage|increase|rise)",
    r"credit\s+(?:downgrade|rating\s+cut|watch\s+negative)",
    r"(?:insolvency|bankruptcy|NCLT\s+admission|winding\s+up)",
    r"(?:delisting|suspension\s+of\s+trading)",
]

import re

def _classify_sentiment_fast(
    text: str,
    category: str = "",
) -> dict[str, Any]:
    """
    Ultra-fast rule-based sentiment classification.
    Runs at ingestion time — no LLM needed.
    Returns label ('bullish', 'bearish', 'neutral') and confidence score.
    """
    combined = f"{text} {category}".lower()

    bullish_hits = 0
    for pattern in BULLISH_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            bullish_hits += 1

    bearish_hits = 0
    for pattern in BEARISH_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            bearish_hits += 1

    total = bullish_hits + bearish_hits

    if total == 0:
        # Default heuristics based on category
        if category in ("dividend", "buyback", "bonus", "corporate_action"):
            return {"label": "bullish", "score": 0.55}
        if category in ("board_meeting", "board_meeting_notice"):
            return {"label": "neutral", "score": 0.0}
        return {"label": "neutral", "score": 0.0}

    if bullish_hits > bearish_hits:
        confidence = min(0.95, 0.5 + (bullish_hits - bearish_hits) * 0.12)
        return {"label": "bullish", "score": round(confidence, 3)}
    elif bearish_hits > bullish_hits:
        confidence = min(0.95, 0.5 + (bearish_hits - bullish_hits) * 0.12)
        return {"label": "bearish", "score": round(-confidence, 3)}
    else:
        return {"label": "neutral", "score": 0.0}
