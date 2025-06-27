from __future__ import annotations

"""Liquidity detection utilities for Smart Money Concepts."""

from typing import Dict, List
import pandas as pd


def identify_liquidity_zones(candles: pd.DataFrame, tolerance: float = 0.0005) -> Dict[str, float | None]:
    """Identify simple liquidity zones such as EQH/EQL and previous day high/low."""
    result = {"eqh": None, "eql": None, "pdh": None, "pdl": None}
    if candles.empty:
        return result
    highs = candles["high"]
    lows = candles["low"]
    if len(highs) < 2:
        return result
    last_day = candles.index[-1].date()
    prev_day_mask = candles.index.date < last_day
    prev_day = candles.loc[prev_day_mask]
    if not prev_day.empty:
        result["pdh"] = float(prev_day["high"].max())
        result["pdl"] = float(prev_day["low"].min())
    recent_highs = highs.tail(10)
    recent_lows = lows.tail(10)
    max_h = recent_highs.max()
    min_h = recent_highs.min()
    if max_h - min_h <= tolerance * max_h:
        result["eqh"] = float(max_h)
    max_l = recent_lows.max()
    min_l = recent_lows.min()
    if max_l - min_l <= tolerance * max_l:
        result["eql"] = float(min_l)
    return result


def detect_fvgs(candles: pd.DataFrame) -> List[Dict[str, float]]:
    """Detect basic fair value gaps (imbalances) between candles."""
    gaps: List[Dict[str, float]] = []
    if len(candles) < 3:
        return gaps
    for i in range(2, len(candles)):
        a = candles.iloc[i - 2]
        b = candles.iloc[i - 1]
        c = candles.iloc[i]
        if b["low"] > a["high"] and c["low"] > b["high"]:
            gaps.append({"index": i, "type": "bullish", "low": b["high"], "high": c["low"]})
        elif b["high"] < a["low"] and c["high"] < b["low"]:
            gaps.append({"index": i, "type": "bearish", "high": b["low"], "low": c["high"]})
    return gaps


def detect_liquidity_voids(candles: pd.DataFrame, threshold: float = 2.0) -> List[int]:
    """Optional detection of large jumps (liquidity voids)."""
    voids: List[int] = []
    if len(candles) < 2:
        return voids
    for i in range(1, len(candles)):
        if abs(candles["close"].iloc[i] - candles["open"].iloc[i]) > threshold * (candles["high"].iloc[i - 1] - candles["low"].iloc[i - 1]):
            voids.append(i)
    return voids


def detect_stop_runs(candles: pd.DataFrame) -> bool:
    """Detect simple stop hunts via wick sweeps of prior highs/lows."""
    if len(candles) < 3:
        return False
    last = candles.iloc[-1]
    prev_high = candles["high"].iloc[-2]
    prev_low = candles["low"].iloc[-2]
    return last["high"] > prev_high and last["close"] < prev_high or last["low"] < prev_low and last["close"] > prev_low