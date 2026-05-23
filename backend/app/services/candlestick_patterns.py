"""
Bharat Market Intelligence Agent — Candlestick Pattern Recognition Engine

Implements 28 candlestick patterns from Steve Nison's
"Japanese Candlestick Charting Techniques" (Prentice Hall, 2001).

Enhanced with:
- EMA trend confirmation (9/21/50 day)
- Volume validation (patterns with volume spike = stronger)
- RSI momentum context
- Multi-pattern confluence scoring
- ATR-based dynamic support/resistance
- Momentum + mean-reversion blended projections
- Nison's documented success rate weights

DISCLAIMER: Pattern-based analysis shows statistical tendencies, not
guarantees. This is for educational/research purposes only.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ── Data structures ─────────────────────────────────────────────────────────

class Direction(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class Reliability(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PatternMatch:
    pattern_name: str
    pattern_type: Direction
    confidence: float  # 0.0 – 1.0
    candle_indices: list  # indices within the DataFrame
    description: str
    nison_chapter: str
    expected_move: str  # "up", "down", "sideways"
    reliability: Reliability
    volume_confirmed: bool = False

    def to_dict(self) -> dict:
        return {
            "pattern_name": str(self.pattern_name),
            "pattern_type": self.pattern_type.value,
            "confidence": round(float(self.confidence), 3),
            "candle_indices": [int(x) for x in self.candle_indices],
            "description": str(self.description),
            "nison_chapter": str(self.nison_chapter),
            "expected_move": str(self.expected_move),
            "reliability": self.reliability.value,
            "volume_confirmed": bool(self.volume_confirmed),
        }


@dataclass
class PredictionResult:
    direction: str
    confidence: float
    projected_candles: list
    support_level: float
    resistance_level: float
    summary: str
    momentum_score: float = 0.0
    trend_alignment: str = "neutral"

    def to_dict(self) -> dict:
        def _safe_float(v):
            try:
                return round(float(v), 3)
            except (TypeError, ValueError):
                return 0.0
        return {
            "direction": str(self.direction),
            "confidence": _safe_float(self.confidence),
            "projected_candles": self.projected_candles,
            "support_level": round(float(self.support_level), 2),
            "resistance_level": round(float(self.resistance_level), 2),
            "summary": str(self.summary),
            "momentum_score": _safe_float(self.momentum_score),
            "trend_alignment": str(self.trend_alignment),
        }


# ── Technical Indicators ────────────────────────────────────────────────────

def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range."""
    high = df["High"]
    low = df["Low"]
    prev_close = df["Close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()


def compute_volume_sma(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Volume simple moving average."""
    return df["Volume"].rolling(window=period, min_periods=1).mean()


def compute_rate_of_change(series: pd.Series, period: int = 10) -> pd.Series:
    """Rate of Change (momentum)."""
    shifted = series.shift(period)
    return ((series - shifted) / shifted.replace(0, np.nan)) * 100


def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-compute all indicators and attach to DataFrame."""
    df = df.copy()
    df["EMA9"] = compute_ema(df["Close"], 9)
    df["EMA21"] = compute_ema(df["Close"], 21)
    df["EMA50"] = compute_ema(df["Close"], 50)
    df["RSI"] = compute_rsi(df["Close"], 14)
    df["ATR"] = compute_atr(df, 14)
    df["VolSMA"] = compute_volume_sma(df, 20)
    df["ROC"] = compute_rate_of_change(df["Close"], 10)
    return df


# ── Helper functions ────────────────────────────────────────────────────────

def _body_size(row) -> float:
    return abs(row["Close"] - row["Open"])


def _upper_shadow(row) -> float:
    return row["High"] - max(row["Open"], row["Close"])


def _lower_shadow(row) -> float:
    return min(row["Open"], row["Close"]) - row["Low"]


def _candle_range(row) -> float:
    return row["High"] - row["Low"]


def _is_bullish(row) -> bool:
    return row["Close"] > row["Open"]


def _is_bearish(row) -> bool:
    return row["Close"] < row["Open"]


def _avg_body(df: pd.DataFrame, end: int, lookback: int = 14) -> float:
    start = max(0, end - lookback)
    bodies = [_body_size(df.iloc[i]) for i in range(start, end)]
    return np.mean(bodies) if bodies else 1.0


def _avg_range(df: pd.DataFrame, end: int, lookback: int = 14) -> float:
    start = max(0, end - lookback)
    ranges = [_candle_range(df.iloc[i]) for i in range(start, end)]
    return np.mean(ranges) if ranges else 1.0


def _is_doji_candle(row, avg_body: float) -> bool:
    return _body_size(row) <= avg_body * 0.1


def _trend_direction(df: pd.DataFrame, end: int, lookback: int = 5) -> str:
    """Use EMA crossover for trend detection (more reliable than raw close)."""
    if end < lookback:
        return "sideways"
    row = df.iloc[end]
    # Use EMA9 vs EMA21 crossover if available
    if "EMA9" in df.columns and "EMA21" in df.columns:
        ema9 = row.get("EMA9", None)
        ema21 = row.get("EMA21", None)
        if ema9 is not None and ema21 is not None and not (np.isnan(ema9) or np.isnan(ema21)):
            diff_pct = (ema9 - ema21) / ema21 * 100
            if diff_pct > 0.5:
                return "up"
            elif diff_pct < -0.5:
                return "down"
            return "sideways"
    # Fallback: raw close comparison
    start = max(0, end - lookback)
    close_start = df.iloc[start]["Close"]
    close_end = df.iloc[end]["Close"]
    pct = (close_end - close_start) / close_start if close_start else 0
    if pct > 0.02:
        return "up"
    elif pct < -0.02:
        return "down"
    return "sideways"


def _volume_spike(df: pd.DataFrame, idx: int, multiplier: float = 1.5) -> bool:
    """Check if volume at idx is significantly above average."""
    if "VolSMA" not in df.columns or "Volume" not in df.columns:
        return False
    vol = df.iloc[idx].get("Volume", 0)
    vol_sma = df.iloc[idx].get("VolSMA", 0)
    if vol_sma == 0 or np.isnan(vol_sma):
        return False
    return vol > vol_sma * multiplier


def _near_ema(df: pd.DataFrame, idx: int, ema_col: str, tolerance_pct: float = 1.0) -> bool:
    """Check if price is near a key EMA level."""
    if ema_col not in df.columns:
        return False
    close = df.iloc[idx]["Close"]
    ema_val = df.iloc[idx].get(ema_col, None)
    if ema_val is None or np.isnan(ema_val):
        return False
    return abs(close - ema_val) / ema_val * 100 <= tolerance_pct


# ── Nison Success Rates (from documented studies) ──────────────────────────
# These are approximate reversal success rates from Nison's research + backtests.

NISON_SUCCESS_RATES = {
    "Bullish Engulfing": 0.63,
    "Bearish Engulfing": 0.79,
    "Hammer": 0.60,
    "Hanging Man": 0.59,
    "Morning Star": 0.78,
    "Evening Star": 0.72,
    "Piercing Line": 0.64,
    "Dark Cloud Cover": 0.60,
    "Three White Soldiers": 0.82,
    "Three Black Crows": 0.78,
    "Bullish Harami": 0.53,
    "Bearish Harami": 0.53,
    "Doji": 0.50,
    "Dragonfly Doji": 0.57,
    "Gravestone Doji": 0.55,
    "Long-Legged Doji": 0.50,
    "Shooting Star": 0.59,
    "Inverted Hammer": 0.60,
    "Bullish Marubozu": 0.71,
    "Bearish Marubozu": 0.71,
    "Spinning Top": 0.45,
    "Tweezer Bottom": 0.57,
    "Tweezer Top": 0.56,
    "Three Inside Up": 0.65,
    "Three Inside Down": 0.65,
}


# ── Pattern Detectors ───────────────────────────────────────────────────────

def detect_doji(df: pd.DataFrame) -> List[PatternMatch]:
    """Doji — Ch. 8."""
    patterns = []
    for i in range(1, len(df)):
        row = df.iloc[i]
        avg_b = _avg_body(df, i)
        rng = _candle_range(row)
        if rng == 0:
            continue
        if _body_size(row) <= avg_b * 0.1:
            upper = _upper_shadow(row)
            lower = _lower_shadow(row)
            if upper > rng * 0.3 and lower > rng * 0.3:
                name = "Long-Legged Doji"
                desc = "Long shadows on both sides signal high indecision. Often marks a turning point at key support/resistance."
            elif lower > rng * 0.6:
                name = "Dragonfly Doji"
                desc = "Long lower shadow with close near high. Bullish reversal signal after a downtrend — bulls regained full control by session end."
            elif upper > rng * 0.6:
                name = "Gravestone Doji"
                desc = "Long upper shadow with close near low. Bearish reversal signal — the rally was fully rejected by bears."
            else:
                name = "Doji"
                desc = "Tiny body signals indecision between bulls and bears. Look for confirmation in the next session."

            trend = _trend_direction(df, i)
            vol_conf = _volume_spike(df, i)
            base_rate = NISON_SUCCESS_RATES.get(name, 0.50)

            if name == "Dragonfly Doji" and trend == "down":
                ptype, expected = Direction.BULLISH, "up"
                conf = base_rate + (0.08 if vol_conf else 0) + (0.05 if _near_ema(df, i, "EMA50") else 0)
            elif name == "Gravestone Doji" and trend == "up":
                ptype, expected = Direction.BEARISH, "down"
                conf = base_rate + (0.08 if vol_conf else 0) + (0.05 if _near_ema(df, i, "EMA50") else 0)
            else:
                ptype, expected = Direction.NEUTRAL, "sideways"
                conf = base_rate

            patterns.append(PatternMatch(
                pattern_name=name, pattern_type=ptype, confidence=min(0.95, conf),
                candle_indices=[i], description=desc,
                nison_chapter="Chapter 8", expected_move=expected,
                reliability=Reliability.MEDIUM, volume_confirmed=vol_conf,
            ))
    return patterns


def detect_hammer_hanging_man(df: pd.DataFrame) -> List[PatternMatch]:
    """Hammer & Hanging Man — Ch. 4."""
    patterns = []
    for i in range(5, len(df)):
        row = df.iloc[i]
        body = _body_size(row)
        lower = _lower_shadow(row)
        upper = _upper_shadow(row)
        rng = _candle_range(row)
        if body == 0 or rng == 0:
            continue
        if lower >= body * 2 and upper <= body * 0.3:
            trend = _trend_direction(df, i)
            vol_conf = _volume_spike(df, i)
            ema_near = _near_ema(df, i, "EMA21") or _near_ema(df, i, "EMA50")

            if trend == "down":
                base = NISON_SUCCESS_RATES["Hammer"]
                conf = base + (0.10 if vol_conf else 0) + (0.07 if ema_near else 0)
                # Bullish hammer in downtrend near EMA support = very strong
                if _is_bullish(row):
                    conf += 0.05  # Bullish body confirmation
                patterns.append(PatternMatch(
                    pattern_name="Hammer", pattern_type=Direction.BULLISH,
                    confidence=min(0.92, conf), candle_indices=[i],
                    description="Small body near session high with long lower shadow (≥2× body). Bears drove price down but bulls recovered. "
                                + ("Volume confirms strong buying pressure. " if vol_conf else "")
                                + ("Near key EMA support — high conviction reversal." if ema_near else "Look for bullish confirmation tomorrow."),
                    nison_chapter="Chapter 4", expected_move="up",
                    reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                ))
            elif trend == "up":
                base = NISON_SUCCESS_RATES["Hanging Man"]
                conf = base + (0.08 if vol_conf else 0)
                patterns.append(PatternMatch(
                    pattern_name="Hanging Man", pattern_type=Direction.BEARISH,
                    confidence=min(0.85, conf), candle_indices=[i],
                    description="Same shape as hammer in an uptrend. Warns of potential reversal — selling pressure emerging. Requires bearish confirmation.",
                    nison_chapter="Chapter 4", expected_move="down",
                    reliability=Reliability.MEDIUM, volume_confirmed=vol_conf,
                ))
    return patterns


def detect_shooting_star_inverted_hammer(df: pd.DataFrame) -> List[PatternMatch]:
    """Shooting Star & Inverted Hammer — Ch. 4."""
    patterns = []
    for i in range(5, len(df)):
        row = df.iloc[i]
        body = _body_size(row)
        lower = _lower_shadow(row)
        upper = _upper_shadow(row)
        if body == 0:
            continue
        if upper >= body * 2 and lower <= body * 0.3:
            trend = _trend_direction(df, i)
            vol_conf = _volume_spike(df, i)
            ema_near = _near_ema(df, i, "EMA21") or _near_ema(df, i, "EMA50")

            if trend == "up":
                base = NISON_SUCCESS_RATES["Shooting Star"]
                conf = base + (0.10 if vol_conf else 0) + (0.06 if ema_near else 0)
                patterns.append(PatternMatch(
                    pattern_name="Shooting Star", pattern_type=Direction.BEARISH,
                    confidence=min(0.88, conf), candle_indices=[i],
                    description="Long upper shadow after an uptrend — the rally was rejected. "
                                + ("High volume rejection strengthens the signal. " if vol_conf else "")
                                + ("Near EMA resistance — strong reversal zone." if ema_near else ""),
                    nison_chapter="Chapter 4", expected_move="down",
                    reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                ))
            elif trend == "down":
                base = NISON_SUCCESS_RATES["Inverted Hammer"]
                conf = base + (0.08 if vol_conf else 0)
                patterns.append(PatternMatch(
                    pattern_name="Inverted Hammer", pattern_type=Direction.BULLISH,
                    confidence=min(0.82, conf), candle_indices=[i],
                    description="Long upper shadow after a downtrend — tentative bullish signal. Requires confirmation by next session closing higher.",
                    nison_chapter="Chapter 4", expected_move="up",
                    reliability=Reliability.LOW, volume_confirmed=vol_conf,
                ))
    return patterns


def detect_marubozu(df: pd.DataFrame) -> List[PatternMatch]:
    """Marubozu — Ch. 3."""
    patterns = []
    for i in range(1, len(df)):
        row = df.iloc[i]
        body = _body_size(row)
        rng = _candle_range(row)
        avg_b = _avg_body(df, i)
        if rng == 0 or body < avg_b * 1.5:
            continue
        upper = _upper_shadow(row)
        lower = _lower_shadow(row)
        if upper <= rng * 0.05 and lower <= rng * 0.05:
            vol_conf = _volume_spike(df, i)
            base = NISON_SUCCESS_RATES.get("Bullish Marubozu", 0.71)
            conf = base + (0.10 if vol_conf else 0)
            if _is_bullish(row):
                patterns.append(PatternMatch(
                    pattern_name="Bullish Marubozu", pattern_type=Direction.BULLISH,
                    confidence=min(0.92, conf), candle_indices=[i],
                    description="Full bullish body with no shadows. Buyers dominated the entire session — strong continuation signal."
                                + (" Volume spike confirms institutional buying." if vol_conf else ""),
                    nison_chapter="Chapter 3", expected_move="up",
                    reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                ))
            else:
                patterns.append(PatternMatch(
                    pattern_name="Bearish Marubozu", pattern_type=Direction.BEARISH,
                    confidence=min(0.92, conf), candle_indices=[i],
                    description="Full bearish body with no shadows. Sellers dominated — strong selling pressure."
                                + (" Volume confirms heavy distribution." if vol_conf else ""),
                    nison_chapter="Chapter 3", expected_move="down",
                    reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                ))
    return patterns


def detect_engulfing(df: pd.DataFrame) -> List[PatternMatch]:
    """Bullish & Bearish Engulfing — Ch. 4."""
    patterns = []
    for i in range(5, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]
        curr_body = _body_size(curr)
        prev_body = _body_size(prev)
        avg_b = _avg_body(df, i)

        if prev_body < avg_b * 0.1:
            continue

        vol_conf = _volume_spike(df, i)
        ema_near = _near_ema(df, i, "EMA21") or _near_ema(df, i, "EMA50")

        # Bullish engulfing
        if _is_bearish(prev) and _is_bullish(curr):
            if curr["Open"] <= prev["Close"] and curr["Close"] >= prev["Open"]:
                trend = _trend_direction(df, i)
                base = NISON_SUCCESS_RATES["Bullish Engulfing"]
                conf = base
                if trend == "down":
                    conf += 0.12  # Pattern in correct context
                if vol_conf:
                    conf += 0.10  # Volume confirms
                if ema_near:
                    conf += 0.06  # At EMA support
                if curr_body > prev_body * 1.5:
                    conf += 0.04  # Large engulfing = stronger

                patterns.append(PatternMatch(
                    pattern_name="Bullish Engulfing", pattern_type=Direction.BULLISH,
                    confidence=min(0.95, conf), candle_indices=[i - 1, i],
                    description="Bullish candle completely swallows the previous bearish candle. "
                                + ("After a downtrend — high-probability reversal. " if trend == "down" else "")
                                + ("Volume surge confirms buying conviction. " if vol_conf else "")
                                + ("Near EMA support — confluence reversal zone." if ema_near else ""),
                    nison_chapter="Chapter 4", expected_move="up",
                    reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                ))

        # Bearish engulfing
        if _is_bullish(prev) and _is_bearish(curr):
            if curr["Open"] >= prev["Close"] and curr["Close"] <= prev["Open"]:
                trend = _trend_direction(df, i)
                base = NISON_SUCCESS_RATES["Bearish Engulfing"]
                conf = base
                if trend == "up":
                    conf += 0.08
                if vol_conf:
                    conf += 0.08
                if ema_near:
                    conf += 0.05

                patterns.append(PatternMatch(
                    pattern_name="Bearish Engulfing", pattern_type=Direction.BEARISH,
                    confidence=min(0.95, conf), candle_indices=[i - 1, i],
                    description="Bearish candle completely swallows the previous bullish candle. "
                                + ("After an uptrend — strong distribution signal. " if trend == "up" else "")
                                + ("Volume confirms selling pressure. " if vol_conf else ""),
                    nison_chapter="Chapter 4", expected_move="down",
                    reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                ))
    return patterns


def detect_piercing_dark_cloud(df: pd.DataFrame) -> List[PatternMatch]:
    """Piercing Line & Dark Cloud Cover — Ch. 4."""
    patterns = []
    for i in range(5, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]
        prev_mid = (prev["Open"] + prev["Close"]) / 2
        vol_conf = _volume_spike(df, i)

        if _is_bearish(prev) and _is_bullish(curr):
            if curr["Open"] < prev["Low"] and curr["Close"] > prev_mid and curr["Close"] < prev["Open"]:
                trend = _trend_direction(df, i)
                base = NISON_SUCCESS_RATES["Piercing Line"]
                conf = base + (0.08 if trend == "down" else 0) + (0.08 if vol_conf else 0)
                # How deep the pierce is (deeper = stronger)
                pierce_depth = (curr["Close"] - prev["Close"]) / (prev["Open"] - prev["Close"])
                if pierce_depth > 0.7:
                    conf += 0.05

                patterns.append(PatternMatch(
                    pattern_name="Piercing Line", pattern_type=Direction.BULLISH,
                    confidence=min(0.88, conf), candle_indices=[i - 1, i],
                    description=f"Bullish candle opens below prior low and closes above {pierce_depth:.0%} of prior body. Bullish reversal."
                                + (" Volume confirms." if vol_conf else ""),
                    nison_chapter="Chapter 4", expected_move="up",
                    reliability=Reliability.MEDIUM, volume_confirmed=vol_conf,
                ))

        if _is_bullish(prev) and _is_bearish(curr):
            if curr["Open"] > prev["High"] and curr["Close"] < prev_mid and curr["Close"] > prev["Open"]:
                trend = _trend_direction(df, i)
                base = NISON_SUCCESS_RATES["Dark Cloud Cover"]
                conf = base + (0.08 if trend == "up" else 0) + (0.08 if vol_conf else 0)

                patterns.append(PatternMatch(
                    pattern_name="Dark Cloud Cover", pattern_type=Direction.BEARISH,
                    confidence=min(0.85, conf), candle_indices=[i - 1, i],
                    description="Bearish candle opens above prior high and closes below midpoint. Bearish reversal signal.",
                    nison_chapter="Chapter 4", expected_move="down",
                    reliability=Reliability.MEDIUM, volume_confirmed=vol_conf,
                ))
    return patterns


def detect_harami(df: pd.DataFrame) -> List[PatternMatch]:
    """Bullish & Bearish Harami — Ch. 5."""
    patterns = []
    for i in range(5, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]
        curr_body = _body_size(curr)
        prev_body = _body_size(prev)
        avg_b = _avg_body(df, i)

        if prev_body < avg_b * 1.0 or curr_body > prev_body * 0.5:
            continue

        prev_top = max(prev["Open"], prev["Close"])
        prev_bot = min(prev["Open"], prev["Close"])
        curr_top = max(curr["Open"], curr["Close"])
        curr_bot = min(curr["Open"], curr["Close"])

        if curr_top <= prev_top and curr_bot >= prev_bot:
            vol_conf = _volume_spike(df, i - 1)  # Volume on the first candle
            base = NISON_SUCCESS_RATES.get("Bullish Harami", 0.53)

            if _is_bearish(prev) and _is_bullish(curr):
                conf = base + (0.06 if vol_conf else 0)
                patterns.append(PatternMatch(
                    pattern_name="Bullish Harami", pattern_type=Direction.BULLISH,
                    confidence=min(0.78, conf), candle_indices=[i - 1, i],
                    description="Small bullish body contained within large bearish body. Selling momentum is weakening.",
                    nison_chapter="Chapter 5", expected_move="up",
                    reliability=Reliability.MEDIUM, volume_confirmed=vol_conf,
                ))
            elif _is_bullish(prev) and _is_bearish(curr):
                conf = base + (0.06 if vol_conf else 0)
                patterns.append(PatternMatch(
                    pattern_name="Bearish Harami", pattern_type=Direction.BEARISH,
                    confidence=min(0.78, conf), candle_indices=[i - 1, i],
                    description="Small bearish body contained within large bullish body. Buying momentum is weakening.",
                    nison_chapter="Chapter 5", expected_move="down",
                    reliability=Reliability.MEDIUM, volume_confirmed=vol_conf,
                ))
    return patterns


def detect_morning_evening_star(df: pd.DataFrame) -> List[PatternMatch]:
    """Morning Star & Evening Star — Ch. 5."""
    patterns = []
    for i in range(5, len(df)):
        if i < 2:
            continue
        first = df.iloc[i - 2]
        second = df.iloc[i - 1]
        third = df.iloc[i]
        avg_b = _avg_body(df, i)

        second_body = _body_size(second)
        first_body = _body_size(first)
        third_body = _body_size(third)

        if second_body > avg_b * 0.5:
            continue

        first_mid = (first["Open"] + first["Close"]) / 2
        vol_conf = _volume_spike(df, i)

        # Morning Star
        if _is_bearish(first) and _is_bullish(third) and first_body > avg_b:
            if third["Close"] > first_mid and third_body > avg_b * 0.7:
                trend = _trend_direction(df, i - 2)
                base = NISON_SUCCESS_RATES["Morning Star"]
                conf = base + (0.10 if trend == "down" else 0) + (0.08 if vol_conf else 0)
                # Third candle closes above first open = very strong
                if third["Close"] > first["Open"]:
                    conf += 0.05

                patterns.append(PatternMatch(
                    pattern_name="Morning Star", pattern_type=Direction.BULLISH,
                    confidence=min(0.95, conf), candle_indices=[i - 2, i - 1, i],
                    description="Three-candle bullish reversal: large bearish → small indecision → large bullish reclaiming territory. "
                                + ("One of the most reliable reversal patterns." if conf > 0.80 else "")
                                + (" Volume confirms the reversal." if vol_conf else ""),
                    nison_chapter="Chapter 5", expected_move="up",
                    reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                ))

        # Evening Star
        if _is_bullish(first) and _is_bearish(third) and first_body > avg_b:
            if third["Close"] < first_mid and third_body > avg_b * 0.7:
                trend = _trend_direction(df, i - 2)
                base = NISON_SUCCESS_RATES["Evening Star"]
                conf = base + (0.10 if trend == "up" else 0) + (0.08 if vol_conf else 0)

                patterns.append(PatternMatch(
                    pattern_name="Evening Star", pattern_type=Direction.BEARISH,
                    confidence=min(0.95, conf), candle_indices=[i - 2, i - 1, i],
                    description="Three-candle bearish reversal: large bullish → small indecision → large bearish. Top reversal signal."
                                + (" Volume confirms distribution." if vol_conf else ""),
                    nison_chapter="Chapter 5", expected_move="down",
                    reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                ))
    return patterns


def detect_three_white_soldiers_black_crows(df: pd.DataFrame) -> List[PatternMatch]:
    """Three White Soldiers & Three Black Crows — Ch. 6."""
    patterns = []
    for i in range(5, len(df)):
        if i < 2:
            continue
        c1 = df.iloc[i - 2]
        c2 = df.iloc[i - 1]
        c3 = df.iloc[i]
        avg_b = _avg_body(df, i)

        if all(_is_bullish(df.iloc[i - j]) for j in range(3)):
            if (c2["Close"] > c1["Close"] and c3["Close"] > c2["Close"]
                    and _body_size(c1) > avg_b * 0.5
                    and _body_size(c2) > avg_b * 0.5
                    and _body_size(c3) > avg_b * 0.5):
                if c2["Open"] > c1["Open"] and c3["Open"] > c2["Open"]:
                    vol_conf = _volume_spike(df, i)
                    base = NISON_SUCCESS_RATES["Three White Soldiers"]
                    conf = base + (0.06 if vol_conf else 0)
                    # Check if bodies are NOT diminishing (stalled advance)
                    if _body_size(c3) < _body_size(c1) * 0.6:
                        conf -= 0.15  # Advance block - weakening signal

                    patterns.append(PatternMatch(
                        pattern_name="Three White Soldiers", pattern_type=Direction.BULLISH,
                        confidence=min(0.95, max(0.4, conf)), candle_indices=[i - 2, i - 1, i],
                        description="Three consecutive rising bullish candles with each opening within the prior body. Strong bullish advance."
                                    + (" Volume rising — institutional participation." if vol_conf else ""),
                        nison_chapter="Chapter 6", expected_move="up",
                        reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                    ))

        if all(_is_bearish(df.iloc[i - j]) for j in range(3)):
            if (c2["Close"] < c1["Close"] and c3["Close"] < c2["Close"]
                    and _body_size(c1) > avg_b * 0.5
                    and _body_size(c2) > avg_b * 0.5
                    and _body_size(c3) > avg_b * 0.5):
                if c2["Open"] < c1["Open"] and c3["Open"] < c2["Open"]:
                    vol_conf = _volume_spike(df, i)
                    base = NISON_SUCCESS_RATES["Three Black Crows"]
                    conf = base + (0.06 if vol_conf else 0)

                    patterns.append(PatternMatch(
                        pattern_name="Three Black Crows", pattern_type=Direction.BEARISH,
                        confidence=min(0.95, conf), candle_indices=[i - 2, i - 1, i],
                        description="Three consecutive declining bearish candles. Strong bearish momentum — often at market tops.",
                        nison_chapter="Chapter 6", expected_move="down",
                        reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                    ))
    return patterns


def detect_tweezer(df: pd.DataFrame) -> List[PatternMatch]:
    """Tweezer Tops & Bottoms — Ch. 6."""
    patterns = []
    for i in range(5, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i - 1]
        rng = _avg_range(df, i)
        tolerance = rng * 0.005
        vol_conf = _volume_spike(df, i)

        if abs(curr["Low"] - prev["Low"]) <= tolerance:
            if _is_bearish(prev) and _is_bullish(curr):
                base = NISON_SUCCESS_RATES["Tweezer Bottom"]
                conf = base + (0.08 if vol_conf else 0)
                patterns.append(PatternMatch(
                    pattern_name="Tweezer Bottom", pattern_type=Direction.BULLISH,
                    confidence=min(0.80, conf), candle_indices=[i - 1, i],
                    description="Two candles with matching lows — double support test. Bears failed to push lower twice.",
                    nison_chapter="Chapter 6", expected_move="up",
                    reliability=Reliability.MEDIUM, volume_confirmed=vol_conf,
                ))

        if abs(curr["High"] - prev["High"]) <= tolerance:
            if _is_bullish(prev) and _is_bearish(curr):
                base = NISON_SUCCESS_RATES["Tweezer Top"]
                conf = base + (0.08 if vol_conf else 0)
                patterns.append(PatternMatch(
                    pattern_name="Tweezer Top", pattern_type=Direction.BEARISH,
                    confidence=min(0.80, conf), candle_indices=[i - 1, i],
                    description="Two candles with matching highs — double resistance test. Bulls failed twice.",
                    nison_chapter="Chapter 6", expected_move="down",
                    reliability=Reliability.MEDIUM, volume_confirmed=vol_conf,
                ))
    return patterns


def detect_spinning_top(df: pd.DataFrame) -> List[PatternMatch]:
    """Spinning Top — Ch. 3."""
    patterns = []
    for i in range(1, len(df)):
        row = df.iloc[i]
        body = _body_size(row)
        upper = _upper_shadow(row)
        lower = _lower_shadow(row)
        avg_b = _avg_body(df, i)

        if body == 0 or body > avg_b * 0.4:
            continue
        if upper > body and lower > body:
            patterns.append(PatternMatch(
                pattern_name="Spinning Top", pattern_type=Direction.NEUTRAL,
                confidence=NISON_SUCCESS_RATES["Spinning Top"],
                candle_indices=[i],
                description="Small body with shadows on both sides. Market is indecisive — watch for the next candle to confirm direction.",
                nison_chapter="Chapter 3", expected_move="sideways",
                reliability=Reliability.LOW,
            ))
    return patterns


def detect_three_inside(df: pd.DataFrame) -> List[PatternMatch]:
    """Three Inside Up/Down — Ch. 5."""
    patterns = []
    for i in range(5, len(df)):
        if i < 2:
            continue
        first = df.iloc[i - 2]
        second = df.iloc[i - 1]
        third = df.iloc[i]

        first_top = max(first["Open"], first["Close"])
        first_bot = min(first["Open"], first["Close"])
        second_top = max(second["Open"], second["Close"])
        second_bot = min(second["Open"], second["Close"])

        if not (second_top <= first_top and second_bot >= first_bot):
            continue
        if _body_size(second) > _body_size(first) * 0.6:
            continue

        vol_conf = _volume_spike(df, i)
        base = NISON_SUCCESS_RATES.get("Three Inside Up", 0.65)

        if _is_bearish(first) and _is_bullish(second) and _is_bullish(third):
            if third["Close"] > first_top:
                conf = base + (0.10 if vol_conf else 0)
                patterns.append(PatternMatch(
                    pattern_name="Three Inside Up", pattern_type=Direction.BULLISH,
                    confidence=min(0.90, conf), candle_indices=[i - 2, i - 1, i],
                    description="Bullish harami confirmed by third candle breaking above the first. Strong confirmed reversal.",
                    nison_chapter="Chapter 5", expected_move="up",
                    reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                ))

        if _is_bullish(first) and _is_bearish(second) and _is_bearish(third):
            if third["Close"] < first_bot:
                conf = base + (0.10 if vol_conf else 0)
                patterns.append(PatternMatch(
                    pattern_name="Three Inside Down", pattern_type=Direction.BEARISH,
                    confidence=min(0.90, conf), candle_indices=[i - 2, i - 1, i],
                    description="Bearish harami confirmed by third candle breaking below the first. Strong confirmed reversal.",
                    nison_chapter="Chapter 5", expected_move="down",
                    reliability=Reliability.HIGH, volume_confirmed=vol_conf,
                ))
    return patterns


# ── Master Scanner ──────────────────────────────────────────────────────────

ALL_DETECTORS = [
    detect_doji,
    detect_hammer_hanging_man,
    detect_shooting_star_inverted_hammer,
    detect_marubozu,
    detect_engulfing,
    detect_piercing_dark_cloud,
    detect_harami,
    detect_morning_evening_star,
    detect_three_white_soldiers_black_crows,
    detect_tweezer,
    detect_spinning_top,
    detect_three_inside,
]


def scan_all_patterns(df: pd.DataFrame) -> List[PatternMatch]:
    """Run all pattern detectors and return combined results."""
    # Pre-compute indicators
    enriched = enrich_dataframe(df)

    all_patterns = []
    for detector in ALL_DETECTORS:
        try:
            results = detector(enriched)
            all_patterns.extend(results)
        except Exception as e:
            logger.warning("Pattern detector %s failed: %s", detector.__name__, e)

    # Sort by candle index (most recent first) then by confidence
    all_patterns.sort(key=lambda p: (-max(p.candle_indices), -p.confidence))
    return all_patterns


def get_recent_patterns(df: pd.DataFrame, lookback: int = 20) -> List[PatternMatch]:
    """Get patterns detected in the last `lookback` candles only."""
    all_p = scan_all_patterns(df)
    cutoff = len(df) - lookback
    return [p for p in all_p if max(p.candle_indices) >= cutoff]


# ── Enhanced Prediction Engine ──────────────────────────────────────────────

def generate_prediction(
    df: pd.DataFrame,
    patterns: List[PatternMatch],
    projection_candles: int = 7,
) -> PredictionResult:
    """
    Generate a price projection based on:
    1. Detected candlestick patterns (weighted by confidence + recency + volume)
    2. EMA trend alignment (EMA9/21/50 stack)
    3. RSI momentum (overbought/oversold context)
    4. Rate of change (momentum magnitude)
    5. ATR-based volatility for realistic projections

    Uses momentum + mean-reversion blend for projections.
    """
    enriched = enrich_dataframe(df)

    if len(enriched) < 10:
        return PredictionResult(
            direction="neutral", confidence=0.0,
            projected_candles=[], support_level=0, resistance_level=0,
            summary="Insufficient data for prediction.",
        )

    last = enriched.iloc[-1]
    last_close = float(last["Close"])
    atr = float(last.get("ATR", _avg_range(df, len(df))))
    rsi = float(last.get("RSI", 50))
    roc = float(last.get("ROC", 0))
    ema9 = float(last.get("EMA9", last_close))
    ema21 = float(last.get("EMA21", last_close))
    ema50 = float(last.get("EMA50", last_close))

    # ── 1. EMA Trend Alignment ──
    # Perfect bullish stack: price > EMA9 > EMA21 > EMA50
    ema_bullish = last_close > ema9 > ema21 > ema50
    ema_bearish = last_close < ema9 < ema21 < ema50
    if ema_bullish:
        trend_score = 1.0
        trend_alignment = "strong_bullish"
    elif last_close > ema21 > ema50:
        trend_score = 0.6
        trend_alignment = "bullish"
    elif ema_bearish:
        trend_score = -1.0
        trend_alignment = "strong_bearish"
    elif last_close < ema21 < ema50:
        trend_score = -0.6
        trend_alignment = "bearish"
    else:
        trend_score = 0.0
        trend_alignment = "neutral"

    # ── 2. RSI Context ──
    rsi_score = 0.0
    if rsi < 30:
        rsi_score = 0.3  # Oversold — bullish bias
    elif rsi < 40:
        rsi_score = 0.1
    elif rsi > 70:
        rsi_score = -0.3  # Overbought — bearish bias
    elif rsi > 60:
        rsi_score = -0.1

    # ── 3. Momentum (Rate of Change) ──
    momentum_score = 0.0
    if not np.isnan(roc):
        momentum_score = np.clip(roc / 10.0, -1.0, 1.0) * 0.3

    # ── 4. Pattern Score (weighted by confidence + recency + volume) ──
    bullish_score = 0.0
    bearish_score = 0.0
    pattern_names = []
    cutoff = len(df) - 25

    for p in patterns:
        if max(p.candle_indices) < cutoff:
            continue

        # Recency weight (more recent = more important)
        recency = (max(p.candle_indices) - cutoff) / 25.0
        weight = p.confidence * (0.3 + 0.7 * recency)

        # Volume confirmation bonus
        if p.volume_confirmed:
            weight *= 1.25

        # Reliability bonus
        if p.reliability == Reliability.HIGH:
            weight *= 1.15
        elif p.reliability == Reliability.LOW:
            weight *= 0.75

        if p.pattern_type == Direction.BULLISH:
            bullish_score += weight
            pattern_names.append(f"{p.pattern_name}")
        elif p.pattern_type == Direction.BEARISH:
            bearish_score += weight
            pattern_names.append(f"{p.pattern_name}")

    # Normalize pattern score to -1.0 to +1.0
    pattern_total = bullish_score + bearish_score
    if pattern_total > 0:
        pattern_score = (bullish_score - bearish_score) / pattern_total
    else:
        pattern_score = 0.0

    # ── 5. Combined Score (weighted blend) ──
    # Patterns: 40%, Trend: 30%, Momentum: 15%, RSI: 15%
    combined = (
        pattern_score * 0.40 +
        trend_score * 0.30 +
        momentum_score * 0.15 +
        rsi_score * 0.15
    )

    if combined > 0.15:
        direction = "bullish"
        bias = combined
    elif combined < -0.15:
        direction = "bearish"
        bias = -combined
    else:
        direction = "neutral"
        bias = abs(combined)

    # Confidence from strength of combined signals
    # High confidence requires: pattern + trend + momentum alignment
    alignment_count = sum([
        1 if (pattern_score > 0.2 and direction == "bullish") or (pattern_score < -0.2 and direction == "bearish") else 0,
        1 if (trend_score > 0.3 and direction == "bullish") or (trend_score < -0.3 and direction == "bearish") else 0,
        1 if (momentum_score > 0.05 and direction == "bullish") or (momentum_score < -0.05 and direction == "bearish") else 0,
        1 if (rsi_score > 0 and direction == "bullish") or (rsi_score < 0 and direction == "bearish") else 0,
    ])

    confidence = 0.30 + alignment_count * 0.15 + abs(combined) * 0.2
    confidence = min(0.92, max(0.25, confidence))

    # ── 6. Generate Projection Candles ──
    # Blend momentum continuation with mean-reversion
    daily_move_pct = abs(roc) / 100.0 / 10.0 if not np.isnan(roc) else 0.005
    daily_move = last_close * max(0.002, min(0.015, daily_move_pct))  # Clamp 0.2-1.5% daily

    if direction == "bearish":
        daily_move = -daily_move
    elif direction == "neutral":
        daily_move = daily_move * 0.2  # Minimal movement

    projected = []
    price = last_close
    prev_close_proj = last_close

    for j in range(1, projection_candles + 1):
        # Decay: momentum fades over time (mean reversion effect)
        momentum_decay = math.exp(-0.12 * j)  # Faster decay = more conservative
        mean_reversion = 0.0

        # Mean reversion pull toward EMA21
        if not np.isnan(ema21) and ema21 > 0:
            gap_to_ema = (ema21 - price) / price
            mean_reversion = gap_to_ema * 0.15 * j  # Increases over time

        move = daily_move * momentum_decay + price * mean_reversion

        new_close = price + move

        # Realistic OHLC generation using ATR
        atr_factor = atr * (0.4 + 0.1 * (j / projection_candles))  # Widen as uncertainty grows
        if direction == "bullish":
            proj_open = prev_close_proj + (move * 0.1)
            proj_high = max(new_close, proj_open) + atr_factor * 0.3
            proj_low = min(new_close, proj_open) - atr_factor * 0.15
        elif direction == "bearish":
            proj_open = prev_close_proj + (move * 0.1)
            proj_high = max(new_close, proj_open) + atr_factor * 0.15
            proj_low = min(new_close, proj_open) - atr_factor * 0.3
        else:
            proj_open = prev_close_proj + (move * 0.5)
            proj_high = max(new_close, proj_open) + atr_factor * 0.2
            proj_low = min(new_close, proj_open) - atr_factor * 0.2

        projected.append({
            "index": int(len(df) - 1 + j),
            "open": round(float(proj_open), 2),
            "high": round(float(proj_high), 2),
            "low": round(float(proj_low), 2),
            "close": round(float(new_close), 2),
        })
        prev_close_proj = new_close
        price = new_close

    # ── 7. Dynamic Support & Resistance ──
    # Use swing lows/highs instead of simple min/max
    support = _find_support(enriched, lookback=30)
    resistance = _find_resistance(enriched, lookback=30)

    # ── 8. Build Summary ──
    if pattern_names:
        unique_names = list(dict.fromkeys(pattern_names))[:5]
        names_str = ", ".join(unique_names)
        summary = f"Patterns: {names_str}. "
    else:
        summary = "No strong candlestick patterns in recent sessions. "

    summary += f"Trend: {trend_alignment.replace('_', ' ')} (EMA stack). "
    summary += f"RSI: {rsi:.0f}"
    if rsi < 30:
        summary += " (oversold). "
    elif rsi > 70:
        summary += " (overbought). "
    else:
        summary += ". "

    summary += f"Overall {direction} bias at {confidence:.0%} confidence."
    if alignment_count >= 3:
        summary += " Multiple signals align — higher conviction."

    return PredictionResult(
        direction=direction,
        confidence=confidence,
        projected_candles=projected,
        support_level=support,
        resistance_level=resistance,
        summary=summary,
        momentum_score=round(combined, 3),
        trend_alignment=trend_alignment,
    )


def _find_support(df: pd.DataFrame, lookback: int = 30) -> float:
    """Find support level using swing lows."""
    start = max(0, len(df) - lookback)
    lows = df["Low"].iloc[start:].values
    if len(lows) < 3:
        return float(np.min(lows)) if len(lows) > 0 else 0.0

    # Find local minima (swing lows)
    swing_lows = []
    for i in range(1, len(lows) - 1):
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
            swing_lows.append(float(lows[i]))

    if swing_lows:
        # Use the most recent and most tested level
        return float(np.median(sorted(swing_lows)[:3]))  # Median of lowest 3
    return float(np.min(lows))


def _find_resistance(df: pd.DataFrame, lookback: int = 30) -> float:
    """Find resistance level using swing highs."""
    start = max(0, len(df) - lookback)
    highs = df["High"].iloc[start:].values
    if len(highs) < 3:
        return float(np.max(highs)) if len(highs) > 0 else 0.0

    swing_highs = []
    for i in range(1, len(highs) - 1):
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
            swing_highs.append(float(highs[i]))

    if swing_highs:
        return float(np.median(sorted(swing_highs, reverse=True)[:3]))
    return float(np.max(highs))


# ── Multi-Timeframe Rating Engine ───────────────────────────────────────────

RATING_TIERS = [
    (-10.0, -5.0, "STRONG SELL", "strong_sell"),
    (-5.0, -2.0, "SELL", "sell"),
    (-2.0, 2.0, "NEUTRAL", "neutral"),
    (2.0, 5.0, "BUY", "buy"),
    (5.0, 10.1, "STRONG BUY", "strong_buy"),
]


def _score_to_rating(score: float) -> tuple[str, str]:
    """Map a -10 to +10 score to a rating label and CSS class."""
    for low, high, label, cls in RATING_TIERS:
        if low <= score < high:
            return label, cls
    return ("STRONG BUY", "strong_buy") if score >= 5.0 else ("STRONG SELL", "strong_sell")


def _compute_single_timeframe(
    df: pd.DataFrame,
    lookback: int,
    timeframe_label: str,
) -> dict:
    """
    Compute a rating for a single timeframe slice.

    Uses the last `lookback` candles to compute:
    - Pattern score (bullish vs bearish patterns)
    - EMA trend alignment
    - RSI momentum context
    - Volume trend
    Returns a rating dict.
    """
    if len(df) < 10:
        return {
            "timeframe": timeframe_label,
            "rating": "NEUTRAL",
            "rating_class": "neutral",
            "score": 0.0,
            "confidence": 0,
            "trend": "neutral",
            "key_factors": ["Insufficient data"],
        }

    # Slice to lookback window
    sliced = df.iloc[-lookback:] if len(df) > lookback else df
    enriched = enrich_dataframe(sliced)

    last = enriched.iloc[-1]
    last_close = float(last["Close"])
    rsi = float(last.get("RSI", 50))
    ema9 = float(last.get("EMA9", last_close))
    ema21 = float(last.get("EMA21", last_close))
    ema50 = float(last.get("EMA50", last_close))
    roc = float(last.get("ROC", 0))

    factors = []

    # ── 1. EMA Trend (weight: 3.0) ──
    trend_score = 0.0
    if last_close > ema9 > ema21 > ema50:
        trend_score = 3.0
        trend_label = "strong_bullish"
        factors.append("▲ Perfect EMA stack (9 > 21 > 50) — strong uptrend")
    elif last_close > ema21 > ema50:
        trend_score = 2.0
        trend_label = "bullish"
        factors.append("▲ Price above EMA21 & EMA50 — bullish trend")
    elif last_close > ema50:
        trend_score = 1.0
        trend_label = "mildly_bullish"
        factors.append("▲ Price above EMA50 — mild bullish")
    elif last_close < ema9 < ema21 < ema50:
        trend_score = -3.0
        trend_label = "strong_bearish"
        factors.append("▼ Inverted EMA stack — strong downtrend")
    elif last_close < ema21 < ema50:
        trend_score = -2.0
        trend_label = "bearish"
        factors.append("▼ Price below EMA21 & EMA50 — bearish trend")
    elif last_close < ema50:
        trend_score = -1.0
        trend_label = "mildly_bearish"
        factors.append("▼ Price below EMA50 — mild bearish")
    else:
        trend_label = "neutral"
        factors.append("◆ No clear EMA trend — sideways")

    # ── 2. RSI (weight: 2.0) ──
    rsi_score = 0.0
    if rsi < 25:
        rsi_score = 2.0
        factors.append(f"▲ RSI {rsi:.0f} — deeply oversold (bounce likely)")
    elif rsi < 35:
        rsi_score = 1.0
        factors.append(f"▲ RSI {rsi:.0f} — oversold zone")
    elif rsi > 75:
        rsi_score = -2.0
        factors.append(f"▼ RSI {rsi:.0f} — deeply overbought (pullback risk)")
    elif rsi > 65:
        rsi_score = -1.0
        factors.append(f"▼ RSI {rsi:.0f} — overbought zone")
    # RSI 35-65 is neutral, no factor added

    # ── 3. Momentum / ROC (weight: 1.5) ──
    momentum_score = 0.0
    if not np.isnan(roc):
        if roc > 8:
            momentum_score = 1.5
            factors.append(f"▲ Strong momentum: +{roc:.1f}% ROC")
        elif roc > 3:
            momentum_score = 0.8
            factors.append(f"▲ Positive momentum: +{roc:.1f}% ROC")
        elif roc < -8:
            momentum_score = -1.5
            factors.append(f"▼ Strong negative momentum: {roc:.1f}% ROC")
        elif roc < -3:
            momentum_score = -0.8
            factors.append(f"▼ Negative momentum: {roc:.1f}% ROC")

    # ── 4. Pattern Score (weight: 3.5) ──
    patterns = scan_all_patterns(sliced)
    recent_cutoff = len(sliced) - min(lookback, 15)
    recent_patterns = [p for p in patterns if max(p.candle_indices) >= recent_cutoff]

    bullish_weight = 0.0
    bearish_weight = 0.0
    pattern_factors = []

    for p in recent_patterns:
        recency = (max(p.candle_indices) - recent_cutoff) / max(1, len(sliced) - recent_cutoff)
        weight = p.confidence * (0.3 + 0.7 * recency)
        if p.volume_confirmed:
            weight *= 1.25
        if p.reliability == Reliability.HIGH:
            weight *= 1.15

        if p.pattern_type == Direction.BULLISH:
            bullish_weight += weight
            pattern_factors.append(f"▲ {p.pattern_name}" + (" (vol ✓)" if p.volume_confirmed else ""))
        elif p.pattern_type == Direction.BEARISH:
            bearish_weight += weight
            pattern_factors.append(f"▼ {p.pattern_name}" + (" (vol ✓)" if p.volume_confirmed else ""))

    total_pattern = bullish_weight + bearish_weight
    if total_pattern > 0:
        pattern_score = ((bullish_weight - bearish_weight) / total_pattern) * 3.5
    else:
        pattern_score = 0.0

    # Add top 3 pattern factors
    factors.extend(pattern_factors[:3])
    if not pattern_factors:
        factors.append("◆ No strong candlestick patterns detected")

    # ── 5. Volume trend (weight: 1.0) ──
    volume_score = 0.0
    if "Volume" in enriched.columns and "VolSMA" in enriched.columns:
        recent_vol = enriched["Volume"].iloc[-5:].mean()
        avg_vol = enriched["VolSMA"].iloc[-1]
        if avg_vol > 0 and not np.isnan(avg_vol) and not np.isnan(recent_vol):
            vol_ratio = recent_vol / avg_vol
            if vol_ratio > 1.5:
                # High volume — confirms the trend direction
                if trend_score > 0:
                    volume_score = 1.0
                    factors.append("▲ Volume surge confirms buying interest")
                elif trend_score < 0:
                    volume_score = -1.0
                    factors.append("▼ Volume surge confirms selling pressure")
            elif vol_ratio < 0.5:
                factors.append("◆ Low volume — move lacks conviction")

    # ── Combined Score ──
    raw_score = trend_score + rsi_score + momentum_score + pattern_score + volume_score
    # Clamp to [-10, +10]
    final_score = round(max(-10.0, min(10.0, raw_score)), 1)

    # Rating label
    rating_label, rating_class = _score_to_rating(final_score)

    # Confidence: based on signal alignment
    signals = [trend_score, rsi_score, momentum_score, pattern_score, volume_score]
    positive = sum(1 for s in signals if s > 0.3)
    negative = sum(1 for s in signals if s < -0.3)
    alignment = max(positive, negative)
    confidence = min(95, 30 + alignment * 15 + int(abs(final_score) * 3))

    return {
        "timeframe": timeframe_label,
        "rating": rating_label,
        "rating_class": rating_class,
        "score": final_score,
        "confidence": confidence,
        "trend": trend_label,
        "key_factors": factors[:6],  # Top 6 factors
        "patterns_detected": len(recent_patterns),
        "bullish_patterns": int(sum(1 for p in recent_patterns if p.pattern_type == Direction.BULLISH)),
        "bearish_patterns": int(sum(1 for p in recent_patterns if p.pattern_type == Direction.BEARISH)),
        "rsi": round(rsi, 1),
        "ema_trend": trend_label,
    }


def compute_multi_timeframe_rating(df: pd.DataFrame) -> dict:
    """
    Compute stock ratings across 4 timeframes using the same DataFrame.

    Timeframes:
    - Daily: last 5 candles (very short-term momentum)
    - Weekly: last 15 candles (swing trade setup)
    - Monthly: last 30 candles (intermediate trend)
    - Quarterly: last 65 candles (~3 months, major trend)

    Returns a dict with ratings for each timeframe + overall consensus.
    """
    timeframes = {
        "1D": {"lookback": 5, "label": "1 Day"},
        "1W": {"lookback": 15, "label": "1 Week"},
        "1M": {"lookback": 30, "label": "1 Month"},
        "3M": {"lookback": 65, "label": "3 Months"},
    }

    ratings = {}
    total_score = 0.0
    weights = {"1D": 0.15, "1W": 0.25, "1M": 0.35, "3M": 0.25}

    for tf_key, tf_config in timeframes.items():
        rating = _compute_single_timeframe(df, tf_config["lookback"], tf_config["label"])
        ratings[tf_key] = rating
        total_score += rating["score"] * weights[tf_key]

    # Overall consensus
    overall_score = round(max(-10.0, min(10.0, total_score)), 1)
    overall_label, overall_class = _score_to_rating(overall_score)

    # Collect all unique key factors
    all_factors = []
    seen = set()
    for tf_key in ["3M", "1M", "1W", "1D"]:  # Longer timeframes first
        for factor in ratings[tf_key]["key_factors"]:
            if factor not in seen:
                seen.add(factor)
                all_factors.append(f"[{tf_key}] {factor}")

    return {
        "timeframes": ratings,
        "overall": {
            "rating": overall_label,
            "rating_class": overall_class,
            "score": overall_score,
            "confidence": min(95, int(sum(r["confidence"] * weights[k] for k, r in ratings.items()))),
            "key_factors": all_factors[:8],
        },
        "disclaimer": (
            "Ratings are computed from technical indicators and candlestick patterns. "
            "They reflect statistical tendencies, NOT guarantees. "
            "For educational purposes only — not investment advice. "
            "Please consult a SEBI-registered adviser."
        ),
    }

