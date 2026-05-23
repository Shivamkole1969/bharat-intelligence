"""
Bharat Market Intelligence Agent — Background Scheduler Worker

Runs scheduled tasks:
- Ingestion pipeline every 15 minutes during market hours (9:00-16:00 IST)
- Signal scoring every 30 minutes
- Health check every 5 minutes
- Stale cache cleanup every hour

Uses APScheduler for production-grade scheduling.
Can run standalone or be imported into the main FastAPI app.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.config import get_settings
from app.utils.helpers import setup_logging

logger = logging.getLogger(__name__)
settings = get_settings()

# IST offset
IST = timezone(timedelta(hours=5, minutes=30))


def _is_market_hours() -> bool:
    """Check if current time is within NSE market hours (9:00 - 16:00 IST)."""
    now_ist = datetime.now(IST)
    hour = now_ist.hour
    weekday = now_ist.weekday()  # 0=Monday, 6=Sunday
    return weekday < 5 and 9 <= hour < 16


async def scheduled_ingestion():
    """
    Run the full ingestion pipeline.
    Fetches from NSE/BSE (Level 1) + news (Level 3/4).
    """
    from app.services.ingestion_pipeline import run_ingestion

    try:
        is_market = _is_market_hours()
        logger.info(
            "Scheduled ingestion starting (market_hours=%s)",
            is_market,
        )

        # During market hours: all sources, frequent
        # After hours: news only, less frequent
        result = await run_ingestion(
            fetch_nse=is_market,
            fetch_bse=is_market,
            fetch_news=True,
            generate_embeddings=True,
        )

        logger.info(
            "Scheduled ingestion complete: %d fetched, %d stored, %d embedded in %.1fs",
            result.get("documents_fetched", 0),
            result.get("documents_stored", 0),
            result.get("embeddings_generated", 0),
            result.get("duration_seconds", 0),
        )
    except Exception as e:
        logger.error("Scheduled ingestion failed: %s", str(e))


async def scheduled_signal_scoring():
    """Recompute signal scores for all companies with recent events."""
    from app.db.session import async_session_factory
    from app.services.signal_scoring import rank_all_signals

    try:
        async with async_session_factory() as db:
            result = await rank_all_signals(db)
            logger.info(
                "Signal scoring complete: %d companies scored",
                result.get("total_companies_scored", 0),
            )
    except Exception as e:
        logger.error("Signal scoring failed: %s", str(e))


async def scheduled_health_check():
    """Run health check and store snapshot."""
    from app.db.session import async_session_factory
    from app.services.health_monitor import run_full_health_check

    try:
        async with async_session_factory() as db:
            result = await run_full_health_check(db)
            await db.commit()
            logger.debug("Health check: %s", result.get("overall_status", "unknown"))
    except Exception as e:
        logger.error("Health check failed: %s", str(e))


async def scheduled_cache_cleanup():
    """Clean up expired semantic cache entries."""
    from app.db.session import async_session_factory
    from app.db.models import SemanticCache
    from sqlalchemy import delete

    try:
        now = datetime.now(timezone.utc)
        async with async_session_factory() as db:
            result = await db.execute(
                delete(SemanticCache).where(
                    SemanticCache.fresh_until < now
                )
            )
            deleted = result.rowcount
            await db.commit()
            if deleted > 0:
                logger.info("Cache cleanup: removed %d expired entries", deleted)
    except Exception as e:
        logger.error("Cache cleanup failed: %s", str(e))


async def scheduled_batch_classify():
    """Classify unprocessed documents into market events."""
    from app.db.session import async_session_factory
    from app.db.models import MarketEvent, RawDocument
    from app.agents.event_classifier import classify_and_create_event
    from sqlalchemy import exists, select

    try:
        async with async_session_factory() as db:
            has_event = exists(
                select(MarketEvent.id).where(
                    MarketEvent.source_document_id == RawDocument.id
                )
            )
            query = (
                select(RawDocument.id)
                .where(~has_event)
                .where(RawDocument.raw_text.is_not(None))
                .limit(50)
            )
            result = await db.execute(query)
            doc_ids = [row[0] for row in result.all()]

            classified = 0
            for doc_id in doc_ids:
                try:
                    event_id = await classify_and_create_event(doc_id, db)
                    if event_id:
                        classified += 1
                except Exception:
                    pass

            await db.commit()
            if classified > 0:
                logger.info("Batch classify: %d/%d documents classified", classified, len(doc_ids))
    except Exception as e:
        logger.error("Batch classification failed: %s", str(e))


# ============================================================
# Main Scheduler Loop (standalone mode)
# ============================================================
async def run_scheduler():
    """
    Run the scheduler as a standalone async loop.

    SPEED-OPTIMIZED Schedule (v2):
    - Base loop: every 2 minutes (120s)
    - Ingestion: every ~4 min (market hours) / every ~10 min (after hours)
    - Classification: INLINE after every ingestion (no separate cycle!)
    - Signal scoring: every ~20 min
    - Health check: every ~2 min
    - Cache cleanup: every ~30 min
    """
    setup_logging(settings.log_level)
    logger.info("=" * 60)
    logger.info("Bharat Market Intelligence — Background Scheduler Started (v2 Speed)")
    logger.info("Base loop: 120s | Market ingestion: ~4min | Classify: inline")
    logger.info("=" * 60)

    iteration = 0
    while True:
        iteration += 1
        now = datetime.now(IST)
        is_market = _is_market_hours()

        try:
            # Every 2 minutes: health check
            if iteration % 1 == 0:
                await scheduled_health_check()

            # Every ~4 min (market) / ~10 min (after): ingestion + INLINE classify
            ingestion_interval = 2 if is_market else 5  # 2*2=4min / 5*2=10min
            if iteration % ingestion_interval == 0:
                await scheduled_ingestion()
                # Classify immediately after ingestion — no delay!
                await scheduled_batch_classify()

            # Every ~20 min: signal scoring
            if iteration % 10 == 0:
                await scheduled_signal_scoring()

            # Every ~30 min: cache cleanup
            if iteration % 15 == 0:
                await scheduled_cache_cleanup()

        except Exception as e:
            logger.error("Scheduler iteration %d failed: %s", iteration, str(e))

        # Sleep 2 minutes between iterations (was 5 min)
        await asyncio.sleep(120)


if __name__ == "__main__":
    asyncio.run(run_scheduler())
