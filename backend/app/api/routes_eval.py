"""
Bharat Market Intelligence Agent — Evaluation API Routes

Endpoints to trigger and review evaluation runs.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvalRun
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/eval", tags=["Evaluation"])


@router.post("/run")
async def trigger_eval_run(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Trigger a full evaluation run against the chat pipeline.

    Tests compliance, content coverage, citation presence,
    disclaimer inclusion, and latency.
    """
    from app.evals.eval_runner import run_evaluation

    try:
        result = await run_evaluation(db)
        return {
            "status": "completed",
            "aggregate": result.get("aggregate", {}),
            "results": result.get("results", []),
        }
    except Exception as e:
        logger.error("Eval run failed: %s", str(e))
        return {"status": "failed", "error": str(e)}


@router.get("/history")
async def get_eval_history(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get recent evaluation run results."""
    result = await db.execute(
        select(EvalRun)
        .order_by(EvalRun.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()

    return {
        "total": len(runs),
        "runs": [
            {
                "id": str(r.id),
                "eval_type": r.eval_type,
                "dataset_name": r.dataset_name,
                "num_samples": r.num_samples,
                "overall_score": r.overall_score,
                "compliance_score": r.compliance_score,
                "retrieval_score": r.retrieval_score,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ],
    }
