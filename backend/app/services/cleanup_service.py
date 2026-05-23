"""
Bharat Market Intelligence Agent — Database Cleanup Service

Zero Bloat Policy: 
Ensures the free-tier SQLite database stays lightning fast by automatically
pruning historical news, filings, and AI analyses older than a specified threshold.
"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketEvent, StockThesis, ChatSession
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)

async def cleanup_old_data(days: int = 7) -> dict[str, int]:
    """
    Delete all StockEvents and StockTheses older than `days`.
    
    Returns:
        Dictionary containing counts of deleted rows.
    """
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).replace(tzinfo=None)
    logger.info(f"Running DB Cleanup: Purging data older than {days} days ({cutoff_date.isoformat()})")

    stats = {
        "events_deleted": 0,
        "theses_deleted": 0
    }

    try:
        async with async_session_factory() as db:
            # 1. Delete old Events (News/Filings)
            events_stmt = delete(MarketEvent).where(MarketEvent.detected_at < cutoff_date)
            events_result = await db.execute(events_stmt)
            stats["events_deleted"] = events_result.rowcount or 0

            # 2. Delete old Theses (AI Analysis)
            theses_stmt = delete(StockThesis).where(StockThesis.generated_at < cutoff_date)
            theses_result = await db.execute(theses_stmt)
            stats["theses_deleted"] = theses_result.rowcount or 0

            # 3. Delete old Chat Sessions
            sessions_stmt = delete(ChatSession).where(ChatSession.updated_at < cutoff_date)
            sessions_result = await db.execute(sessions_stmt)
            stats["sessions_deleted"] = sessions_result.rowcount or 0

            await db.commit()

        logger.info(f"DB Cleanup complete. Purged {stats['events_deleted']} events, {stats['theses_deleted']} theses, and {stats['sessions_deleted']} sessions.")
        return stats

    except Exception as e:
        logger.error(f"Failed to execute DB cleanup: {str(e)}")
        return stats
