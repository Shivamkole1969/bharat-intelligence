"""
Bharat Market Intelligence Agent — Utility Functions

Hashing, text cleaning, retry logic, and time helpers.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ============================================================
# Hashing Utilities
# ============================================================
def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content for deduplication."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def compute_audit_hash(
    action: str,
    entity_type: str,
    entity_id: str,
    input_data: str,
    output_data: str,
    previous_hash: str,
) -> str:
    """
    Compute hash for audit log chain integrity.
    Each entry's hash depends on the previous entry's hash,
    creating a tamper-evident chain.
    """
    payload = f"{action}|{entity_type}|{entity_id}|{input_data}|{output_data}|{previous_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ============================================================
# Text Cleaning
# ============================================================
def clean_text(text: str) -> str:
    """Clean raw text: normalize whitespace, strip control chars."""
    if not text:
        return ""
    # Remove control characters except newlines and tabs
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length, adding ellipsis if truncated."""
    if not text or len(text) <= max_length:
        return text or ""
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def normalize_query(query: str) -> str:
    """Normalize a search query for cache lookup."""
    query = query.lower().strip()
    query = re.sub(r"\s+", " ", query)
    query = re.sub(r"[^\w\s]", "", query)
    return query


# ============================================================
# Time Utilities
# ============================================================
def utc_now() -> datetime:
    """Get current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time string (e.g., '5 minutes ago')."""
    now = utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    seconds = int(delta.total_seconds())

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 604800:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return dt.strftime("%Y-%m-%d %H:%M UTC")


# ============================================================
# Retry Logic
# ============================================================
def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator for retry with exponential backoff.
    Used for external API calls and database operations.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(
                            base_delay * (2**attempt), max_delay
                        )
                        logger.warning(
                            "Retry %d/%d for %s after error: %s. "
                            "Waiting %.1f seconds.",
                            attempt + 1,
                            max_retries,
                            func.__name__,
                            str(e),
                            delay,
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "All %d retries exhausted for %s: %s",
                            max_retries,
                            func.__name__,
                            str(e),
                        )
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


# ============================================================
# Logging Setup
# ============================================================
def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
