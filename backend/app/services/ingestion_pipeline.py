"""
Bharat Market Intelligence Agent — Ingestion Pipeline Orchestrator

Speed Hierarchy:
  Level 1: NSE + BSE Exchange Filings (0s delay — legally mandated source)
  Level 3: MoneyControl, CNBC-TV18, ET, NDTV Profit (1-5 min delay)
  Level 4: LiveMint, Business Standard (5-30 min delay)

Coordinates the full ingestion workflow:
1. Fetch from Level 1 sources FIRST (NSE + BSE)
2. Then Level 3-4 news aggregators
3. Process documents (normalize, deduplicate, chunk)
4. Tag sentiment (bullish/bearish) at ingestion time
5. Generate embeddings
6. Store everything in the database

Can run as a one-shot job or on a schedule.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.services.bse_scraper import fetch_all_bse_pages
from app.services.document_processor import process_and_store_document
from app.services.embedding_service import embed_unprocessed_chunks
from app.services.news_ingestion import fetch_all_news_feeds
from app.services.nse_scraper import fetch_all_nse_filings
from app.utils.helpers import utc_now

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Orchestrates the complete data ingestion pipeline.

    Speed-first architecture:
    1. Level 1: NSE + BSE exchange filings (instantaneous)
    2. Level 3-4: News aggregators (minutes behind)
    3. Process, embed, store
    """

    def __init__(self):
        self.stats: dict[str, int] = {
            "sources_attempted": 0,
            "level_1_exchange_filings": 0,
            "level_3_aggregator_articles": 0,
            "level_4_mainstream_articles": 0,
            "documents_fetched": 0,
            "documents_stored": 0,
            "documents_duplicate": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "sentiment_tagged": 0,
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "errors": 0,
        }
        self.start_time: Optional[datetime] = None

    async def run_full_pipeline(
        self,
        fetch_nse: bool = True,
        fetch_bse: bool = True,
        fetch_news: bool = True,
        generate_embeddings: bool = True,
    ) -> dict[str, Any]:
        """
        Run the complete ingestion pipeline.

        Fetch order (speed-first):
        1. NSE corporate filings (Level 1 — fastest)
        2. BSE announcements (Level 1 — fastest)
        3. News RSS feeds (Level 3-4 — aggregators)

        Args:
            fetch_nse: Whether to fetch NSE filings (Level 1)
            fetch_bse: Whether to fetch BSE announcements (Level 1)
            fetch_news: Whether to fetch news feeds (Level 3-4)
            generate_embeddings: Whether to generate embeddings

        Returns:
            Pipeline run statistics
        """
        self.start_time = utc_now()
        logger.info("=" * 60)
        logger.info("Starting ingestion pipeline at %s", self.start_time.isoformat())
        logger.info("Priority: Level 1 (Exchanges) → Level 3-4 (News)")
        logger.info("=" * 60)

        all_documents: list[dict[str, Any]] = []

        # ── Level 1: Exchange Sources (Fastest — 0 second delay) ─────
        if fetch_nse:
            nse_docs = await self._fetch_nse()
            all_documents.extend(nse_docs)
            self.stats["level_1_exchange_filings"] += len(nse_docs)

        if fetch_bse:
            bse_docs = await self._fetch_bse()
            all_documents.extend(bse_docs)
            self.stats["level_1_exchange_filings"] += len(bse_docs)

        # ── Level 3-4: News Aggregators (Minutes delay) ──────────────
        if fetch_news:
            news_docs = await self._fetch_news()
            all_documents.extend(news_docs)

            # Count by tier
            for doc in news_docs:
                tier = doc.get("source_tier", 4)
                if tier == 3:
                    self.stats["level_3_aggregator_articles"] += 1
                else:
                    self.stats["level_4_mainstream_articles"] += 1

        self.stats["documents_fetched"] = len(all_documents)

        # Count sentiment distribution
        for doc in all_documents:
            label = doc.get("sentiment_label", "neutral")
            if label == "bullish":
                self.stats["bullish_count"] += 1
            elif label == "bearish":
                self.stats["bearish_count"] += 1
            else:
                self.stats["neutral_count"] += 1
            if label in ("bullish", "bearish"):
                self.stats["sentiment_tagged"] += 1

        logger.info(
            "Total documents fetched: %d (L1: %d, L3: %d, L4: %d)",
            len(all_documents),
            self.stats["level_1_exchange_filings"],
            self.stats["level_3_aggregator_articles"],
            self.stats["level_4_mainstream_articles"],
        )
        logger.info(
            "Sentiment: 📈 %d bullish, 📉 %d bearish, ➖ %d neutral",
            self.stats["bullish_count"],
            self.stats["bearish_count"],
            self.stats["neutral_count"],
        )

        # ── Step 2: Process and store documents ──────────────────────
        # Level 1 docs are first in the list → processed first
        if all_documents:
            await self._process_documents(all_documents)

        # ── Step 3: Generate embeddings ──────────────────────────────
        if generate_embeddings:
            await self._generate_embeddings()

        # ── Step 4: Zero Bloat Policy (Database Cleanup) ─────────────
        from app.services.cleanup_service import cleanup_old_data
        cleanup_stats = await cleanup_old_data(days=7)

        # Calculate duration
        duration = (utc_now() - self.start_time).total_seconds()

        result = {
            **self.stats,
            "duration_seconds": round(duration, 2),
            "started_at": self.start_time.isoformat(),
            "completed_at": utc_now().isoformat(),
            "speed_hierarchy": {
                "level_1_exchange": self.stats["level_1_exchange_filings"],
                "level_3_aggregator": self.stats["level_3_aggregator_articles"],
                "level_4_mainstream": self.stats["level_4_mainstream_articles"],
            },
            "sentiment_summary": {
                "bullish": self.stats["bullish_count"],
                "bearish": self.stats["bearish_count"],
                "neutral": self.stats["neutral_count"],
            },
        }

        logger.info("=" * 60)
        logger.info("Pipeline complete in %.1fs", duration)
        for key, value in self.stats.items():
            logger.info("  %s: %s", key, value)
        logger.info("=" * 60)

        return result

    async def _fetch_nse(self) -> list[dict[str, Any]]:
        """
        Fetch NSE corporate filings — LEVEL 1 (fastest source).
        Corporate announcements + board meetings + corporate actions.
        """
        self.stats["sources_attempted"] += 1
        try:
            documents = await fetch_all_nse_filings()
            logger.info(
                "NSE Level-1: fetched %d filings (announcements + meetings + actions)",
                len(documents),
            )
            return documents
        except Exception as e:
            logger.error("NSE Level-1 fetch failed: %s", str(e))
            self.stats["errors"] += 1
            return []

    async def _fetch_bse(self) -> list[dict[str, Any]]:
        """
        Fetch BSE corporate announcements — LEVEL 1 (fastest source).
        """
        self.stats["sources_attempted"] += 1
        try:
            now = datetime.now()
            from_date = now.strftime("%d/%m/%Y")
            to_date = now.strftime("%d/%m/%Y")

            documents = await fetch_all_bse_pages(
                from_date=from_date,
                to_date=to_date,
                max_pages=5,
            )
            logger.info("BSE Level-1: fetched %d announcements", len(documents))
            return documents
        except Exception as e:
            logger.error("BSE Level-1 fetch failed: %s", str(e))
            self.stats["errors"] += 1
            return []

    async def _fetch_news(self) -> list[dict[str, Any]]:
        """
        Fetch news from RSS feeds — LEVEL 3-4 (aggregators + mainstream).
        """
        self.stats["sources_attempted"] += 1
        try:
            documents = await fetch_all_news_feeds()
            logger.info(
                "News Level-3/4: fetched %d articles from 9 feeds",
                len(documents),
            )
            return documents
        except Exception as e:
            logger.error("News feeds fetch failed: %s", str(e))
            self.stats["errors"] += 1
            return []

    async def _process_documents(self, documents: list[dict[str, Any]]) -> None:
        """Process and store all fetched documents."""
        async with async_session_factory() as db:
            for doc in documents:
                try:
                    doc_id = await process_and_store_document(doc, db)
                    if doc_id:
                        self.stats["documents_stored"] += 1
                    else:
                        self.stats["documents_duplicate"] += 1
                except Exception as e:
                    logger.error(
                        "Failed to process document '%s': %s",
                        doc.get("title", "")[:50],
                        str(e),
                    )
                    self.stats["errors"] += 1

            await db.commit()

    async def _generate_embeddings(self) -> None:
        """Generate embeddings for unprocessed chunks."""
        try:
            async with async_session_factory() as db:
                count = await embed_unprocessed_chunks(db, batch_size=50)
                self.stats["embeddings_generated"] = count
        except Exception as e:
            logger.error("Embedding generation failed: %s", str(e))
            self.stats["errors"] += 1


async def run_ingestion(
    fetch_nse: bool = True,
    fetch_bse: bool = True,
    fetch_news: bool = True,
    generate_embeddings: bool = True,
) -> dict[str, Any]:
    """
    Convenience function to run the full pipeline.

    Can be called from:
    - CLI script
    - Scheduled task (APScheduler)
    - API endpoint (admin trigger)
    """
    pipeline = IngestionPipeline()
    return await pipeline.run_full_pipeline(
        fetch_nse=fetch_nse,
        fetch_bse=fetch_bse,
        fetch_news=fetch_news,
        generate_embeddings=generate_embeddings,
    )
