"""
Bharat Market Intelligence Agent — BSE Announcement Scraper

Fetches corporate announcements from BSE India's public API.
Handles pagination, rate limiting, and deduplication via content hash.

Legal: Only fetches publicly available corporate filings data.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.utils.helpers import clean_text, compute_content_hash

logger = logging.getLogger(__name__)

BSE_ANNOUNCEMENTS_URL = "https://api.bseindia.com/BseIndiaAPI/api/AnnSubCategoryGetData/w"
BSE_ANNOUNCEMENT_DETAIL_URL = "https://www.bseindia.com/xml-data/corpfiling/AttachLive"

# Rate limiting: BSE has strict rate limits
REQUEST_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_DELAY = 2.0

# Common headers to mimic a browser (required by BSE)
BSE_HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": "https://www.bseindia.com/corporates/ann.html",
    "Origin": "https://www.bseindia.com",
}


async def fetch_bse_announcements(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    scrip_code: Optional[str] = None,
    category: str = "-1",
    subcategory: str = "-1",
    page_no: int = 1,
) -> list[dict[str, Any]]:
    """
    Fetch corporate announcements from BSE India API.

    Args:
        from_date: Start date in DD/MM/YYYY format
        to_date: End date in DD/MM/YYYY format
        scrip_code: BSE script code (e.g., '500325' for Reliance)
        category: Announcement category (-1 for all)
        subcategory: Announcement subcategory (-1 for all)
        page_no: Page number for pagination

    Returns:
        List of announcement dictionaries
    """
    now = datetime.now()
    if not from_date:
        from_date = now.strftime("%d/%m/%Y")
    if not to_date:
        to_date = now.strftime("%d/%m/%Y")

    params = {
        "pageno": str(page_no),
        "strCat": category,
        "strPrevDate": from_date,
        "strScrip": scrip_code or "",
        "strSearch": "P",
        "strToDate": to_date,
        "strType": "C",
        "subcategory": subcategory,
    }

    announcements = []

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                BSE_ANNOUNCEMENTS_URL,
                params=params,
                headers=BSE_HEADERS,
            )
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict) or "Table" not in data:
                logger.warning("Unexpected BSE API response structure")
                return []

            raw_announcements = data.get("Table", [])

            for ann in raw_announcements:
                parsed = _parse_bse_announcement(ann)
                if parsed:
                    announcements.append(parsed)

            logger.info(
                "Fetched %d BSE announcements (page %d, %s to %s)",
                len(announcements), page_no, from_date, to_date
            )

    except httpx.HTTPStatusError as e:
        logger.error("BSE API HTTP error: %d %s", e.response.status_code, str(e))
    except httpx.TimeoutException:
        logger.error("BSE API request timed out")
    except Exception as e:
        logger.error("BSE API request failed: %s", str(e))

    return announcements


def _parse_bse_announcement(raw: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Parse a single BSE announcement into a normalized format."""
    try:
        headline = clean_text(raw.get("NEWSSUB", "") or "")
        if not headline:
            return None

        company_name = clean_text(raw.get("SLONGNAME", "") or "")
        scrip_code = str(raw.get("SCRIP_CD", "") or "").strip()
        news_dt = raw.get("NEWS_DT", "")
        attachment_name = raw.get("ATTACHMENTNAME", "")
        category = raw.get("CATEGORYNAME", "")
        subcategory = raw.get("SUBCATEGORYNAME", "")

        # Parse date
        published_at = None
        if news_dt:
            try:
                # BSE date format: "2026-05-22T10:30:00"
                published_at = datetime.fromisoformat(news_dt.replace("Z", "+00:00"))
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        # Build attachment URL
        attachment_url = None
        if attachment_name:
            attachment_url = f"{BSE_ANNOUNCEMENT_DETAIL_URL}/{attachment_name}"

        # Content hash for deduplication
        hash_content = f"{scrip_code}|{headline}|{news_dt}"
        content_hash = compute_content_hash(hash_content)

        # Real-time sentiment classification (imported from NSE scraper)
        from app.services.nse_scraper import _classify_sentiment_fast
        sentiment = _classify_sentiment_fast(headline, category)

        return {
            "source": "bse_exchange",
            "source_tier": 1,  # Level 1: Exchange source
            "source_latency": "exchange_instant",
            "source_url": f"https://www.bseindia.com/corporates/ann.html?scrip={scrip_code}",
            "company_name": company_name,
            "bse_code": scrip_code,
            "document_type": "exchange_filing",
            "title": headline,
            "category": category,
            "subcategory": subcategory,
            "raw_text": headline,
            "published_at": published_at,
            "ingested_at": datetime.now(timezone.utc),
            "content_hash": content_hash,
            "attachment_url": attachment_url,
            "sentiment_label": sentiment["label"],
            "sentiment_score": sentiment["score"],
            "metadata": {
                "exchange": "BSE",
                "bse_scrip_code": scrip_code,
                "category": category,
                "subcategory": subcategory,
                "attachment": attachment_name,
                "news_id": str(raw.get("NEWSID", "")),
                "source_tier": 1,
            },
        }
    except Exception as e:
        logger.error("Failed to parse BSE announcement: %s", str(e))
        return None


async def fetch_all_bse_pages(
    from_date: str,
    to_date: str,
    max_pages: int = 10,
) -> list[dict[str, Any]]:
    """
    Fetch multiple pages of BSE announcements.

    Args:
        from_date: Start date DD/MM/YYYY
        to_date: End date DD/MM/YYYY
        max_pages: Maximum pages to fetch

    Returns:
        All announcements across pages
    """
    all_announcements = []
    seen_hashes: set[str] = set()

    for page in range(1, max_pages + 1):
        page_announcements = await fetch_bse_announcements(
            from_date=from_date,
            to_date=to_date,
            page_no=page,
        )

        if not page_announcements:
            break

        # Deduplicate
        new_count = 0
        for ann in page_announcements:
            h = ann["content_hash"]
            if h not in seen_hashes:
                seen_hashes.add(h)
                all_announcements.append(ann)
                new_count += 1

        logger.info("Page %d: %d new, %d total", page, new_count, len(all_announcements))

        # If fewer than expected, we've reached the end
        if len(page_announcements) < 20:
            break

    return all_announcements
