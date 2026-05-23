"""
Bharat Market Intelligence Agent — News Ingestion Service

Fetches financial news from public RSS feeds and news APIs.
Normalizes into the standard document format for downstream processing.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Optional

import httpx

from app.utils.helpers import clean_text, compute_content_hash

logger = logging.getLogger(__name__)

# Public RSS feeds for Indian financial news
# Ordered by speed tier: faster sources first
RSS_FEEDS = {
    # ── Level 3: Fast Aggregators (1-5 min delay) ──
    "moneycontrol_market": {
        "url": "https://www.moneycontrol.com/rss/marketreports.xml",
        "source_name": "MoneyControl",
        "category": "market_reports",
        "source_tier": 3,
        "source_latency": "aggregator_fast",
    },
    "moneycontrol_news": {
        "url": "https://www.moneycontrol.com/rss/latestnews.xml",
        "source_name": "MoneyControl",
        "category": "latest_news",
        "source_tier": 3,
        "source_latency": "aggregator_fast",
    },
    "cnbctv18_market": {
        "url": "https://www.cnbctv18.com/commonfeeds/v1/cne/rss/market-buzz.xml",
        "source_name": "CNBC-TV18",
        "category": "market_buzz",
        "source_tier": 3,
        "source_latency": "aggregator_fast",
    },
    "ndtv_profit": {
        "url": "https://feeds.feedburner.com/ndtvprofit-latest",
        "source_name": "NDTV Profit",
        "category": "latest",
        "source_tier": 3,
        "source_latency": "aggregator_fast",
    },
    "et_markets": {
        "url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "source_name": "Economic Times",
        "category": "markets",
        "source_tier": 3,
        "source_latency": "aggregator_fast",
    },
    "et_companies": {
        "url": "https://economictimes.indiatimes.com/industry/rssfeeds/13352306.cms",
        "source_name": "Economic Times",
        "category": "companies",
        "source_tier": 3,
        "source_latency": "aggregator_fast",
    },
    # ── Level 4: Mainstream News (5-30 min delay) ──
    "livemint_market": {
        "url": "https://www.livemint.com/rss/markets",
        "source_name": "LiveMint",
        "category": "markets",
        "source_tier": 4,
        "source_latency": "mainstream_news",
    },
    "livemint_companies": {
        "url": "https://www.livemint.com/rss/companies",
        "source_name": "LiveMint",
        "category": "companies",
        "source_tier": 4,
        "source_latency": "mainstream_news",
    },
    "business_standard": {
        "url": "https://www.business-standard.com/rss/markets-106.rss",
        "source_name": "Business Standard",
        "category": "markets",
        "source_tier": 4,
        "source_latency": "mainstream_news",
    },
}

REQUEST_TIMEOUT = 20.0
USER_AGENT = "BharatMarketIntel/1.0 (Research Bot; +https://github.com/bharat-intel)"


async def fetch_rss_feed(
    feed_url: str,
    source_name: str,
    category: str = "news",
) -> list[dict[str, Any]]:
    """
    Fetch and parse an RSS feed into normalized news items.

    Args:
        feed_url: URL of the RSS feed
        source_name: Name of the source (e.g., 'MoneyControl')
        category: News category

    Returns:
        List of normalized news items
    """
    articles = []

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(
                feed_url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/rss+xml, application/xml, text/xml",
                },
            )
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.text)

            # Handle both RSS 2.0 and Atom feeds
            items = root.findall(".//item") or root.findall(
                ".//{http://www.w3.org/2005/Atom}entry"
            )

            for item in items:
                parsed = _parse_rss_item(item, source_name, category, feed_url)
                if parsed:
                    articles.append(parsed)

            logger.info(
                "Fetched %d articles from %s (%s)",
                len(articles), source_name, category
            )

    except httpx.HTTPStatusError as e:
        logger.error("RSS feed HTTP error for %s: %d", feed_url, e.response.status_code)
    except httpx.TimeoutException:
        logger.error("RSS feed timeout: %s", feed_url)
    except ET.ParseError as e:
        logger.error("RSS XML parse error for %s: %s", feed_url, str(e))
    except Exception as e:
        logger.error("RSS feed fetch failed for %s: %s", feed_url, str(e))

    return articles


def _parse_rss_item(
    item: ET.Element,
    source_name: str,
    category: str,
    feed_url: str,
    source_tier: int = 3,
    source_latency: str = "aggregator_fast",
) -> Optional[dict[str, Any]]:
    """Parse a single RSS item into normalized format with sentiment tagging."""
    try:
        # RSS 2.0 tags
        title = _get_text(item, "title")
        link = _get_text(item, "link")
        description = _get_text(item, "description")
        pub_date = _get_text(item, "pubDate")

        # Atom fallback
        if not title:
            title = _get_text(item, "{http://www.w3.org/2005/Atom}title")
        if not link:
            link_elem = item.find("{http://www.w3.org/2005/Atom}link")
            if link_elem is not None:
                link = link_elem.get("href", "")
        if not description:
            description = _get_text(item, "{http://www.w3.org/2005/Atom}summary")

        if not title:
            return None

        title = clean_text(title)
        description = clean_text(description or "")

        # Strip HTML tags from description
        description = re.sub(r"<[^>]+>", "", description)
        description = clean_text(description)

        # Parse publication date
        published_at = None
        if pub_date:
            try:
                published_at = parsedate_to_datetime(pub_date)
                # Convert to UTC and make it naive for PostgreSQL TIMESTAMP WITHOUT TIME ZONE
                if published_at.tzinfo is not None:
                    published_at = published_at.astimezone(timezone.utc).replace(tzinfo=None)
            except (ValueError, TypeError):
                try:
                    published_at = datetime.fromisoformat(
                        pub_date.replace("Z", "+00:00")
                    )
                    if published_at.tzinfo is not None:
                        published_at = published_at.astimezone(timezone.utc).replace(tzinfo=None)
                except (ValueError, TypeError):
                    pass

        # Content hash for deduplication
        hash_content = f"{source_name}|{title}|{link or ''}"
        content_hash = compute_content_hash(hash_content)

        # Real-time sentiment classification
        from app.services.nse_scraper import _classify_sentiment_fast
        full_text = f"{title} {description}" if description else title
        sentiment = _classify_sentiment_fast(full_text, category)

        return {
            "source": source_name.lower().replace(" ", "_"),
            "source_tier": source_tier,
            "source_latency": source_latency,
            "source_url": link or feed_url,
            "document_type": "news",
            "title": title,
            "raw_text": f"{title}\n\n{description}" if description else title,
            "published_at": published_at,
            "ingested_at": datetime.now(timezone.utc),
            "content_hash": content_hash,
            "sentiment_label": sentiment["label"],
            "sentiment_score": sentiment["score"],
            "metadata": {
                "source_name": source_name,
                "category": category,
                "feed_url": feed_url,
                "source_tier": source_tier,
            },
        }
    except Exception as e:
        logger.error("Failed to parse RSS item: %s", str(e))
        return None


def _get_text(element: ET.Element, tag: str) -> Optional[str]:
    """Safely extract text from an XML element."""
    child = element.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return None


async def fetch_all_news_feeds() -> list[dict[str, Any]]:
    """
    Fetch all configured RSS feeds and return deduplicated articles.
    Sorted by source_tier (fastest first).

    Returns:
        All unique news articles across feeds
    """
    all_articles = []
    seen_hashes: set[str] = set()

    # Sort feeds by tier (fastest first)
    sorted_feeds = sorted(
        RSS_FEEDS.items(),
        key=lambda x: x[1].get("source_tier", 4),
    )

    for feed_key, feed_config in sorted_feeds:
        articles = await fetch_rss_feed(
            feed_url=feed_config["url"],
            source_name=feed_config["source_name"],
            category=feed_config["category"],
        )

        # Patch tier/latency into articles
        tier = feed_config.get("source_tier", 4)
        latency = feed_config.get("source_latency", "mainstream_news")
        for article in articles:
            article["source_tier"] = tier
            article["source_latency"] = latency
            if "metadata" in article:
                article["metadata"]["source_tier"] = tier

            h = article["content_hash"]
            if h not in seen_hashes:
                seen_hashes.add(h)
                all_articles.append(article)

    logger.info("Total unique news articles fetched: %d", len(all_articles))
    return all_articles
