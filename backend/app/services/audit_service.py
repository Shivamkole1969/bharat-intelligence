"""
Bharat Market Intelligence Agent — Audit Log Service

Append-only audit log with SHA-256 hash chaining for tamper evidence.
Every significant system action is recorded with:
- Actor (user, agent, system)
- Action performed
- Entity affected
- Input/output hashes
- Chain hash linking to previous entry
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog
from app.utils.helpers import compute_audit_hash, utc_now

logger = logging.getLogger(__name__)


async def write_audit_log(
    db: AsyncSession,
    actor_type: str,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    input_data: str = "",
    output_data: str = "",
    metadata: Optional[dict] = None,
) -> UUID:
    """
    Write a tamper-evident audit log entry.

    The hash chain ensures that any modification to historical entries
    can be detected by recomputing and verifying the chain.

    Args:
        db: Database session
        actor_type: "user", "agent", "system", "scheduler"
        action: Action name (e.g., "ingest_document", "classify_event")
        entity_type: Type of entity (e.g., "document", "event", "company")
        entity_id: ID of the affected entity
        actor_id: ID of the actor (user ID, agent name, etc.)
        input_data: Hash-worthy description of input
        output_data: Hash-worthy description of output
        metadata: Additional JSON metadata

    Returns:
        UUID of the new audit log entry
    """
    # Get the previous entry's hash for chain integrity
    prev_result = await db.execute(
        select(AuditLog.current_hash)
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )
    prev_row = prev_result.scalar_one_or_none()
    previous_hash = prev_row or "genesis"

    # Compute input/output hashes
    from app.utils.helpers import compute_content_hash
    input_hash = compute_content_hash(input_data) if input_data else ""
    output_hash = compute_content_hash(output_data) if output_data else ""

    # Compute chain hash
    current_hash = compute_audit_hash(
        action=action,
        entity_type=entity_type or "",
        entity_id=entity_id or "",
        input_data=input_hash,
        output_data=output_hash,
        previous_hash=previous_hash,
    )

    entry = AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        input_hash=input_hash,
        output_hash=output_hash,
        previous_hash=previous_hash,
        current_hash=current_hash,
        metadata_json=metadata or {},
    )
    db.add(entry)
    await db.flush()

    logger.debug(
        "Audit: [%s] %s.%s by %s/%s → %s",
        action, entity_type, entity_id, actor_type, actor_id, current_hash[:12]
    )

    return entry.id


async def verify_audit_chain(
    db: AsyncSession,
    limit: int = 1000,
) -> dict[str, Any]:
    """
    Verify the integrity of the audit log hash chain.

    Recomputes each entry's hash and checks it matches the stored hash.
    Also verifies that each entry's previous_hash matches the prior entry.

    Returns:
        Verification result with status and any broken links
    """
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.asc())
        .limit(limit)
    )
    entries = result.scalars().all()

    if not entries:
        return {"status": "empty", "total_entries": 0, "verified": 0, "broken": []}

    verified = 0
    broken = []
    expected_prev_hash = "genesis"

    for entry in entries:
        # Check previous hash link
        if entry.previous_hash != expected_prev_hash:
            broken.append({
                "entry_id": str(entry.id),
                "action": entry.action,
                "issue": "previous_hash_mismatch",
                "expected": expected_prev_hash[:16],
                "found": (entry.previous_hash or "")[:16],
            })

        # Recompute and verify current hash
        recomputed = compute_audit_hash(
            action=entry.action,
            entity_type=entry.entity_type or "",
            entity_id=entry.entity_id or "",
            input_data=entry.input_hash or "",
            output_data=entry.output_hash or "",
            previous_hash=entry.previous_hash or "",
        )

        if recomputed != entry.current_hash:
            broken.append({
                "entry_id": str(entry.id),
                "action": entry.action,
                "issue": "hash_tampering_detected",
                "stored": entry.current_hash[:16],
                "recomputed": recomputed[:16],
            })
        else:
            verified += 1

        expected_prev_hash = entry.current_hash

    status = "valid" if not broken else "integrity_violation"

    return {
        "status": status,
        "total_entries": len(entries),
        "verified": verified,
        "broken_count": len(broken),
        "broken": broken[:20],  # Cap output
        "checked_at": utc_now().isoformat(),
    }


# ============================================================
# Convenience Loggers for Common Actions
# ============================================================
async def log_ingestion(
    db: AsyncSession,
    source: str,
    documents_count: int,
    duration_seconds: float,
) -> UUID:
    """Log a data ingestion run."""
    return await write_audit_log(
        db=db,
        actor_type="system",
        action="data_ingestion",
        entity_type="pipeline",
        entity_id=source,
        input_data=f"source={source}",
        output_data=f"documents={documents_count}",
        metadata={
            "source": source,
            "documents_ingested": documents_count,
            "duration_seconds": duration_seconds,
        },
    )


async def log_classification(
    db: AsyncSession,
    document_id: str,
    event_type: str,
    confidence: float,
) -> UUID:
    """Log an event classification."""
    return await write_audit_log(
        db=db,
        actor_type="agent",
        actor_id="event_classifier",
        action="classify_event",
        entity_type="document",
        entity_id=document_id,
        output_data=f"type={event_type},conf={confidence:.2f}",
        metadata={
            "event_type": event_type,
            "confidence": confidence,
        },
    )


async def log_chat_query(
    db: AsyncSession,
    user_id: Optional[str],
    query: str,
    model_used: str,
    latency_ms: int,
) -> UUID:
    """Log a chat query for audit."""
    return await write_audit_log(
        db=db,
        actor_type="user" if user_id else "anonymous",
        actor_id=user_id,
        action="chat_query",
        entity_type="chat",
        input_data=query[:200],  # Truncate for hashing
        output_data=f"model={model_used},latency={latency_ms}ms",
        metadata={
            "model_used": model_used,
            "latency_ms": latency_ms,
        },
    )
