"""
Bharat Market Intelligence Agent — Ingestion API Routes

Admin endpoints to trigger and monitor data ingestion.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentChunk, MarketEvent, RawDocument
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/ingest/trigger")
async def trigger_ingestion(
    fetch_nse: bool = True,
    fetch_bse: bool = True,
    fetch_news: bool = True,
    generate_embeddings: bool = False,
) -> dict:
    """
    Trigger a full ingestion pipeline run.

    Speed hierarchy:
    - Level 1: NSE + BSE exchange filings (fastest — legally mandated source)
    - Level 3: MoneyControl, CNBC-TV18, ET, NDTV Profit (1-5 min delay)
    - Level 4: LiveMint, Business Standard (5-30 min delay)

    All items are automatically tagged with bullish/bearish sentiment.
    """
    from app.services.ingestion_pipeline import run_ingestion

    try:
        result = await run_ingestion(
            fetch_nse=fetch_nse,
            fetch_bse=fetch_bse,
            fetch_news=fetch_news,
            generate_embeddings=generate_embeddings,
        )
        return {
            "status": "completed",
            "result": result,
        }
    except Exception as e:
        logger.error("Ingestion trigger failed: %s", str(e))
        return {
            "status": "failed",
            "error": str(e),
        }


@router.get("/stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get system-wide statistics."""
    # Count documents
    doc_count = await db.execute(select(func.count(RawDocument.id)))
    total_docs = doc_count.scalar() or 0

    # Count chunks
    chunk_count = await db.execute(select(func.count(DocumentChunk.id)))
    total_chunks = chunk_count.scalar() or 0

    # Count chunks with embeddings
    embedded_count = await db.execute(
        select(func.count(DocumentChunk.id)).where(
            DocumentChunk.embedding.is_not(None)
        )
    )
    total_embedded = embedded_count.scalar() or 0

    # Count events
    event_count = await db.execute(select(func.count(MarketEvent.id)))
    total_events = event_count.scalar() or 0

    # Events by type
    event_types = await db.execute(
        select(MarketEvent.event_type, func.count(MarketEvent.id))
        .group_by(MarketEvent.event_type)
        .order_by(func.count(MarketEvent.id).desc())
    )

    # Events by impact
    event_impacts = await db.execute(
        select(MarketEvent.impact_label, func.count(MarketEvent.id))
        .group_by(MarketEvent.impact_label)
        .order_by(func.count(MarketEvent.id).desc())
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "documents": {
            "total": total_docs,
            "chunks": total_chunks,
            "embedded": total_embedded,
            "embedding_coverage": round(
                total_embedded / total_chunks * 100, 1
            ) if total_chunks > 0 else 0,
        },
        "events": {
            "total": total_events,
            "by_type": {
                row[0]: row[1] for row in event_types.all()
            },
            "by_impact": {
                row[0]: row[1] for row in event_impacts.all()
            },
        },
    }


@router.post("/classify/batch")
async def classify_unprocessed_documents(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Classify raw documents that don't have associated market events yet.
    """
    from app.agents.event_classifier import classify_and_create_event
    from sqlalchemy import and_, exists

    # Find documents without events
    has_event = exists(
        select(MarketEvent.id).where(
            MarketEvent.source_document_id == RawDocument.id
        )
    )
    query = (
        select(RawDocument.id)
        .where(~has_event)
        .where(RawDocument.raw_text.is_not(None))
        .limit(limit)
    )
    result = await db.execute(query)
    doc_ids = [row[0] for row in result.all()]

    if not doc_ids:
        return {"status": "no_unprocessed_documents", "classified": 0}

    classified = 0
    errors = 0
    for doc_id in doc_ids:
        try:
            event_id = await classify_and_create_event(doc_id, db)
            if event_id:
                classified += 1
        except Exception as e:
            logger.error("Classification failed for %s: %s", doc_id, str(e))
            errors += 1

    await db.commit()

    return {
        "status": "completed",
        "total_unprocessed": len(doc_ids),
        "classified": classified,
        "errors": errors,
    }
