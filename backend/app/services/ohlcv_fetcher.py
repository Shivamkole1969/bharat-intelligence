"""
Bharat Market Intelligence Agent — Multi-Source OHLCV Data Fetcher

Fetches historical OHLCV data from multiple sources:
1. Groww Public Charting API (reliable, no auth)
2. NSE India API (official exchange)
3. Yahoo Finance via yfinance (fallback)

All normalize to DataFrame with: Open, High, Low, Close, Volume
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Tuple

import httpx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PERIOD_DAYS = {
    "1mo": 30, "3mo": 90, "6mo": 180,
    "1y": 365, "2y": 730, "5y": 1825,
}

# No brotli — Docker doesn't have it
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
}


# ── Source 1: Groww Public API ──────────────────────────────────────────────

def _fetch_groww(symbol: str, period: str) -> pd.DataFrame:
    """
    Groww's public charting API — no auth, no rate limits.
    Returns daily OHLCV candles.
    """
    days = PERIOD_DAYS.get(period, 180)
    end_ts = int(time.time() * 1000)
    start_ts = end_ts - (days * 86400 * 1000)

    url = (
        f"https://groww.in/v1/api/charting_service/v4/chart/exchange/NSE"
        f"/segment/CASH/{symbol.upper()}"
    )
    params = {
        "endTimeInMillis": str(end_ts),
        "startTimeInMillis": str(start_ts),
        "intervalInMinutes": "1440",
    }
    headers = {
        **HEADERS,
        "Referer": "https://groww.in/",
        "Origin": "https://groww.in",
    }

    with httpx.Client(
        timeout=15.0,
        headers=headers,
        follow_redirects=True,
    ) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    candles = data.get("candles", [])
    if not candles:
        raise Exception("Groww: empty candles array")

    rows = []
    for c in candles:
        if len(c) >= 5:
            rows.append({
                "Date": pd.to_datetime(datetime.fromtimestamp(c[0])),
                "Open": float(c[1]),
                "High": float(c[2]),
                "Low": float(c[3]),
                "Close": float(c[4]),
                "Volume": int(c[5]) if len(c) > 5 else 0,
            })

    if not rows:
        raise Exception("Groww: no parseable candles")

    df = pd.DataFrame(rows).sort_values("Date").drop_duplicates("Date").set_index("Date")
    return df


# ── Source 2: NSE India ─────────────────────────────────────────────────────

def _fetch_nse(symbol: str, period: str) -> pd.DataFrame:
    """NSE India official equity history API."""
    days = min(PERIOD_DAYS.get(period, 180), 365)
    to_dt = datetime.now()
    from_dt = to_dt - timedelta(days=days)

    headers = {
        **HEADERS,
        "Referer": "https://www.nseindia.com/get-quotes/equity",
    }

    with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
        # Get cookies first
        try:
            client.get("https://www.nseindia.com")
            time.sleep(0.5)
        except Exception:
            pass

        resp = client.get(
            "https://www.nseindia.com/api/historical/cm/equity",
            params={
                "symbol": symbol.upper(),
                "from": from_dt.strftime("%d-%m-%Y"),
                "to": to_dt.strftime("%d-%m-%Y"),
            },
        )
        resp.raise_for_status()
        data = resp.json()

    rows = []
    for rec in data.get("data", []):
        try:
            rows.append({
                "Date": pd.to_datetime(rec["CH_TIMESTAMP"]),
                "Open": float(rec["CH_OPENING_PRICE"]),
                "High": float(rec["CH_TRADE_HIGH_PRICE"]),
                "Low": float(rec["CH_TRADE_LOW_PRICE"]),
                "Close": float(rec["CH_CLOSING_PRICE"]),
                "Volume": int(float(rec.get("CH_TOT_TRADED_QTY", 0))),
            })
        except (ValueError, TypeError, KeyError):
            continue

    if not rows:
        raise Exception("NSE: no data returned")

    df = pd.DataFrame(rows).sort_values("Date").drop_duplicates("Date").set_index("Date")
    return df


# ── Source 3: Yahoo Finance ─────────────────────────────────────────────────

def _fetch_yahoo(symbol: str, period: str) -> Tuple[str, pd.DataFrame]:
    """Yahoo Finance via yfinance — last resort."""
    import yfinance as yf

    for suffix in [".NS", ".BO"]:
        ticker_sym = f"{symbol}{suffix}"
        for attempt in range(3):
            try:
                df = yf.Ticker(ticker_sym).history(period=period)
                if not df.empty and len(df) > 5:
                    return ticker_sym, df
                break
            except Exception as e:
                if any(k in str(e).lower() for k in ["rate", "429", "too many"]):
                    time.sleep(min(15, 2 ** (attempt + 1)))
                    continue
                raise

    raise Exception("Yahoo: no data")


# ── Master Fetcher ──────────────────────────────────────────────────────────

def fetch_ohlcv_multi_source(
    symbol: str,
    period: str = "6mo",
) -> Tuple[str, str, pd.DataFrame]:
    """
    Fetch OHLCV from multiple sources. Returns (ticker, company_name, DataFrame).
    """
    sym = symbol.upper().strip().replace(" ", "")
    errors = []

    # 1. Groww
    try:
        logger.info("[Groww] Fetching %s...", sym)
        df = _fetch_groww(sym, period)
        if len(df) >= 10:
            logger.info("[Groww] ✓ %d candles for %s", len(df), sym)
            return f"{sym}.NS", sym, df
        errors.append(f"Groww: {len(df)} candles")
    except Exception as e:
        errors.append(f"Groww: {str(e)[:100]}")
        logger.warning("[Groww] Failed: %s", str(e)[:120])

    # 2. NSE
    try:
        logger.info("[NSE] Fetching %s...", sym)
        df = _fetch_nse(sym, period)
        if len(df) >= 10:
            logger.info("[NSE] ✓ %d candles for %s", len(df), sym)
            return f"{sym}.NS", sym, df
        errors.append(f"NSE: {len(df)} candles")
    except Exception as e:
        errors.append(f"NSE: {str(e)[:100]}")
        logger.warning("[NSE] Failed: %s", str(e)[:120])

    # 3. Yahoo
    try:
        logger.info("[Yahoo] Fetching %s...", sym)
        ticker, df = _fetch_yahoo(sym, period)
        if len(df) >= 10:
            logger.info("[Yahoo] ✓ %d candles for %s", len(df), sym)
            name = sym
            try:
                import yfinance as yf
                info = yf.Ticker(ticker).info or {}
                name = info.get("longName") or info.get("shortName") or sym
            except Exception:
                pass
            return ticker, name, df
        errors.append(f"Yahoo: {len(df)} candles")
    except Exception as e:
        errors.append(f"Yahoo: {str(e)[:100]}")
        logger.warning("[Yahoo] Failed: %s", str(e)[:120])

    raise Exception(
        f"All sources failed for {sym}: {' | '.join(errors)}"
    )
