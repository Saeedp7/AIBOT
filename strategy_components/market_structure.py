
from __future__ import annotations

"""Basic market structure detection utilities."""

import pandas as pd
from typing import List, Tuple, Dict


def get_swing_highs_lows(candles: pd.DataFrame, lookback: int = 3) -> Tuple[List[int], List[int]]:
    """Return indices of swing highs and lows using fractal method."""
    highs: List[int] = []
    lows: List[int] = []
    if len(candles) < lookback * 2 + 1:
        return highs, lows
    for i in range(lookback, len(candles) - lookback):
        high = candles["high"].iloc[i]
        low = candles["low"].iloc[i]
        if high == max(candles["high"].iloc[i - lookback : i + lookback + 1]):
            highs.append(i)
        if low == min(candles["low"].iloc[i - lookback : i + lookback + 1]):
            lows.append(i)
    return highs, lows


def detect_bos_mss(candles: pd.DataFrame) -> Dict[str, str | int | None]:
    """Detect simple Break of Structure (BoS) and Market Structure Shift (MSS)."""
    result = {"bos": None, "mss": None, "index": None}
    if len(candles) < 5:
        return result
    highs, lows = get_swing_highs_lows(candles)
    if not highs or not lows:
        return result
    last_high = highs[-1]
    last_low = lows[-1]
    last_close = candles["close"].iloc[-1]
    if last_close > candles["high"].iloc[last_high]:
        result["bos"] = "bullish"
        result["index"] = len(candles) - 1
    elif last_close < candles["low"].iloc[last_low]:
        result["bos"] = "bearish"
        result["index"] = len(candles) - 1

    prev_trend = "bullish" if candles["close"].iloc[last_high] > candles["close"].iloc[last_low] else "bearish"
    if result["bos"] and result["bos"] != prev_trend:
        result["mss"] = result["bos"]
    return result