"""
Bharat Market Intelligence Agent — Health Monitoring Service

Checks the health of all system components:
- Database connectivity
- Redis connectivity
- Kafka/Redpanda connectivity
- LLM provider availability
- Embedding model status
- Ingestion pipeline freshness

Records health snapshots in the system_health table.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import MarketEvent, RawDocument, SystemHealth
from app.utils.helpers import utc_now

logger = logging.getLogger(__name__)
settings = get_settings()


async def check_database(db: AsyncSession) -> dict[str, Any]:
    """Check database connectivity and performance."""
    start = time.time()
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        latency = int((time.time() - start) * 1000)
        return {"status": "healthy", "latency_ms": latency}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "latency_ms": -1}


async def check_redis() -> dict[str, Any]:
    """Check Redis connectivity."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url, decode_responses=True)
        start = time.time()
        await r.ping()
        latency = int((time.time() - start) * 1000)
        await r.aclose()
        return {"status": "healthy", "latency_ms": latency}
    except ImportError:
        return {"status": "not_configured", "error": "redis package not installed"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


async def check_kafka() -> dict[str, Any]:
    """Check Kafka/Redpanda connectivity."""
    try:
        import httpx
        # Check Redpanda's admin API
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"http://{settings.kafka_bootstrap_servers.replace(':9092', ':18082')}/topics")
            if response.status_code == 200:
                return {"status": "healthy"}
            return {"status": "degraded", "http_status": response.status_code}
    except Exception:
        return {"status": "not_configured"}


async def check_llm_providers() -> dict[str, Any]:
    """Check LLM provider availability."""
    providers = {}

    # Check Groq
    if settings.groq_api_key:
        providers["groq"] = {"status": "configured", "model": settings.groq_default_model}
    else:
        providers["groq"] = {"status": "not_configured"}

    # Check OpenAI
    if settings.openai_api_key:
        providers["openai"] = {"status": "configured"}
    else:
        providers["openai"] = {"status": "not_configured"}

    # Check Ollama
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.ollama_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                providers["ollama"] = {"status": "healthy", "models": models[:5]}
            else:
                providers["ollama"] = {"status": "unhealthy"}
    except Exception:
        providers["ollama"] = {"status": "not_reachable"}

    return providers


async def check_data_freshness(db: AsyncSession) -> dict[str, Any]:
    """Check how fresh the ingested data is."""
    now = utc_now()

    # Latest document
    latest_doc = await db.execute(
        select(func.max(RawDocument.ingested_at))
    )
    last_ingested = latest_doc.scalar()

    # Latest event
    latest_event = await db.execute(
        select(func.max(MarketEvent.detected_at))
    )
    last_event = latest_event.scalar()

    # Document count in last 24h
    cutoff_24h = (now - timedelta(hours=24)).replace(tzinfo=None)
    doc_count_24h = await db.execute(
        select(func.count(RawDocument.id)).where(
            RawDocument.ingested_at >= cutoff_24h
        )
    )
    docs_24h = doc_count_24h.scalar() or 0

    # Event count in last 24h
    event_count_24h = await db.execute(
        select(func.count(MarketEvent.id)).where(
            MarketEvent.detected_at >= cutoff_24h
        )
    )
    events_24h = event_count_24h.scalar() or 0

    freshness = {
        "last_document_ingested": last_ingested.isoformat() if last_ingested else None,
        "last_event_detected": last_event.isoformat() if last_event else None,
        "documents_last_24h": docs_24h,
        "events_last_24h": events_24h,
    }

    # Determine freshness status
    if last_ingested:
        age_hours = (now - last_ingested.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        if age_hours < 1:
            freshness["status"] = "fresh"
        elif age_hours < 6:
            freshness["status"] = "acceptable"
        elif age_hours < 24:
            freshness["status"] = "stale"
        else:
            freshness["status"] = "very_stale"
        freshness["data_age_hours"] = round(age_hours, 1)
    else:
        freshness["status"] = "no_data"

    return freshness


async def run_full_health_check(db: AsyncSession) -> dict[str, Any]:
    """
    Run comprehensive health check across all subsystems.
    Stores results in system_health table.
    """
    results = {}

    # Database
    results["database"] = await check_database(db)

    # Redis
    results["redis"] = await check_redis()

    # Kafka
    results["kafka"] = await check_kafka()

    # LLM providers
    results["llm_providers"] = await check_llm_providers()

    # Data freshness
    results["data_freshness"] = await check_data_freshness(db)

    # Overall status
    critical_services = ["database"]
    overall = "healthy"
    for svc in critical_services:
        if results.get(svc, {}).get("status") != "healthy":
            overall = "degraded"
            break

    results["overall_status"] = overall
    results["checked_at"] = utc_now().isoformat()

    # Store snapshot in system_health table
    try:
        for service_name, service_data in results.items():
            if isinstance(service_data, dict) and "status" in service_data:
                entry = SystemHealth(
                    service_name=service_name,
                    status=service_data.get("status", "unknown"),
                    latency_ms=service_data.get("latency_ms"),
                    metadata_json=service_data,
                )
                db.add(entry)
        await db.flush()
    except Exception as e:
        logger.error("Failed to store health snapshot: %s", str(e))

    return results
