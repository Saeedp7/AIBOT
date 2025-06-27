from __future__ import annotations

"""Detection of Smart Money patterns."""

from typing import List, Dict
import pandas as pd


def detect_po3(candles: pd.DataFrame) -> bool:
    """Simplistic PO3 detection: accumulation → manipulation → expansion."""
    if len(candles) < 20:
        return False
    recent = candles.tail(20)
    accum = recent.head(10)
    expand = recent.tail(5)
    return accum["close"].std() < expand["close"].std() and expand["close"].iloc[-1] != expand["open"].iloc[-1]


def detect_three_drives(candles: pd.DataFrame) -> bool:
    """Detect three drives into liquidity using highs or lows."""
    if len(candles) < 7:
        return False
    highs = candles["high"].tail(7)
    lows = candles["low"].tail(7)
    return highs.is_monotonic_increasing or lows.is_monotonic_decreasing


def detect_inside_bars(candles: pd.DataFrame) -> bool:
    """Return True if latest candle is an inside bar."""
    if len(candles) < 2:
        return False
    prev, curr = candles.iloc[-2], candles.iloc[-1]
    return curr["high"] <= prev["high"] and curr["low"] >= prev["low"]