"""
Bharat Market Intelligence Agent — Candlestick Analysis API Routes

Uses multi-source OHLCV fetcher (NSE India direct + Yahoo Finance fallback).
Runs the Nison pattern engine and returns patterns + prediction projections.

Multi-layer cache: in-memory (10 min) + Redis (60 min).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/candlestick", tags=["Candlestick Analysis"])

# ── In-memory cache ──
_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 600  # 10 min
REDIS_CACHE_TTL = 3600  # 60 min


def _cache_key(symbol: str, period: str, interval: str) -> str:
    return f"candlestick:{symbol}:{period}:{interval}"


def _get_cached(key: str) -> Optional[dict]:
    if key in _cache:
        ts, data = _cache[key]
        if time.time() - ts < CACHE_TTL:
            return data
        del _cache[key]
    return None


def _set_cached(key: str, data: dict) -> None:
    _cache[key] = (time.time(), data)
    if len(_cache) > 300:
        oldest = min(_cache, key=lambda k: _cache[k][0])
        del _cache[oldest]


async def _get_redis_cached(key: str) -> Optional[dict]:
    try:
        redis_url = os.environ.get("REDIS_URL", "").strip()
        if not redis_url:
            return None
        import redis.asyncio as aioredis
        r = aioredis.from_url(redis_url, db=2, decode_responses=True)
        data = await r.get(key)
        await r.aclose()
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


async def _set_redis_cached(key: str, data: dict) -> None:
    try:
        redis_url = os.environ.get("REDIS_URL", "").strip()
        if not redis_url:
            return
        import redis.asyncio as aioredis
        r = aioredis.from_url(redis_url, db=2, decode_responses=True)
        await r.setex(key, REDIS_CACHE_TTL, json.dumps(data, default=str))
        await r.aclose()
    except Exception:
        pass


@router.get("/{symbol}")
async def get_candlestick_analysis(
    symbol: str,
    period: str = Query("6mo", description="Data period: 1mo, 3mo, 6mo, 1y, 2y"),
    interval: str = Query("1d", description="Candle interval: 1d, 1wk"),
) -> dict:
    """
    Analyze candlestick patterns for a given NSE/BSE company.
    Uses NSE India direct API as primary source (no rate limits).
    Falls back to Yahoo Finance if NSE fails.
    """
    allowed_periods = {"1mo", "3mo", "6mo", "1y", "2y", "5y"}
    allowed_intervals = {"1d", "1wk"}
    if period not in allowed_periods:
        raise HTTPException(400, f"Invalid period. Use: {', '.join(sorted(allowed_periods))}")
    if interval not in allowed_intervals:
        raise HTTPException(400, f"Invalid interval. Use: {', '.join(sorted(allowed_intervals))}")

    clean_symbol = symbol.upper().strip().replace(" ", "")
    cache_key = _cache_key(clean_symbol, period, interval)

    # Layer 1: In-memory cache
    cached = _get_cached(cache_key)
    if cached:
        return cached

    # Layer 2: Redis cache
    redis_cached = await _get_redis_cached(cache_key)
    if redis_cached:
        _set_cached(cache_key, redis_cached)
        return redis_cached

    # Layer 3: Fetch fresh data from multi-source fetcher
    try:
        from app.services.ohlcv_fetcher import fetch_ohlcv_multi_source

        ticker_symbol, company_name, df = await asyncio.get_event_loop().run_in_executor(
            None, fetch_ohlcv_multi_source, clean_symbol, period
        )

        if df.empty or len(df) < 10:
            raise HTTPException(
                404,
                f"Insufficient price data for {clean_symbol}. "
                "Only found {len(df)} data points."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("OHLCV fetch failed for %s: %s", clean_symbol, str(e))
        raise HTTPException(
            503,
            f"Price data temporarily unavailable for {clean_symbol}. {str(e)}"
        )

    # Run pattern recognition
    from app.services.candlestick_patterns import (
        get_recent_patterns,
        generate_prediction,
        scan_all_patterns,
    )

    all_patterns = scan_all_patterns(df)
    recent_patterns = get_recent_patterns(df, lookback=30)
    prediction = generate_prediction(df, all_patterns)

    # Convert OHLCV to JSON
    ohlcv_data = []
    for idx, row in df.iterrows():
        date_str = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)
        ohlcv_data.append({
            "date": date_str,
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
            "volume": int(row.get("Volume", 0)),
        })

    result = {
        "symbol": clean_symbol,
        "company_name": company_name,
        "ticker_used": ticker_symbol,
        "data_source": "NSE India" if ".NS" in ticker_symbol and "yfinance" not in ticker_symbol else "Yahoo Finance",
        "period": period,
        "interval": interval,
        "data_points": len(ohlcv_data),
        "ohlcv": ohlcv_data,
        "detected_patterns": [p.to_dict() for p in recent_patterns],
        "total_patterns_scanned": len(all_patterns),
        "prediction": prediction.to_dict(),
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "Based on Steve Nison's 'Japanese Candlestick Charting Techniques'. "
            "Patterns show statistical tendencies, NOT guarantees. "
            "For educational purposes only — not investment advice."
        ),
    }

    # Cache in both layers
    _set_cached(cache_key, result)
    await _set_redis_cached(cache_key, result)

    return result


@router.get("/{symbol}/rating")
async def get_stock_rating(
    symbol: str,
    period: str = Query("1y", description="Data period: 6mo, 1y, 2y"),
) -> dict:
    """
    Multi-timeframe stock rating for a given NSE/BSE company.

    Returns ratings across 4 timeframes (1D, 1W, 1M, 3M) based on:
    - Candlestick patterns (Nison methodology)
    - EMA trend alignment (9/21/50)
    - RSI momentum
    - Volume confirmation
    - Rate of change

    NOT investment advice. For educational purposes only.
    """
    allowed_periods = {"6mo", "1y", "2y"}
    if period not in allowed_periods:
        raise HTTPException(400, f"Invalid period. Use: {', '.join(sorted(allowed_periods))}")

    clean_symbol = symbol.upper().strip().replace(" ", "")
    cache_key = f"rating:{clean_symbol}:{period}"

    # Layer 1: In-memory cache
    cached = _get_cached(cache_key)
    if cached:
        return cached

    # Layer 2: Redis cache
    redis_cached = await _get_redis_cached(cache_key)
    if redis_cached:
        _set_cached(cache_key, redis_cached)
        return redis_cached

    # Fetch OHLCV data
    try:
        from app.services.ohlcv_fetcher import fetch_ohlcv_multi_source

        ticker_symbol, company_name, df = await asyncio.get_event_loop().run_in_executor(
            None, fetch_ohlcv_multi_source, clean_symbol, period
        )

        if df.empty or len(df) < 15:
            raise HTTPException(
                404,
                f"Insufficient price data for {clean_symbol} to compute ratings."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("OHLCV fetch failed for rating %s: %s", clean_symbol, str(e))
        raise HTTPException(
            503,
            f"Price data temporarily unavailable for {clean_symbol}."
        )

    # Compute multi-timeframe rating
    from app.services.candlestick_patterns import compute_multi_timeframe_rating

    rating_result = compute_multi_timeframe_rating(df)

    result = {
        "symbol": clean_symbol,
        "company_name": company_name,
        "data_points": len(df),
        "period": period,
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        **rating_result,
    }

    # Cache
    _set_cached(cache_key, result)
    await _set_redis_cached(cache_key, result)

    return result

