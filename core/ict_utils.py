from __future__ import annotations

"""Simplified ICT (Inner Circle Trader) pattern utilities."""

import pandas as pd


def detect_liquidity_grab(df: pd.DataFrame) -> bool:
    """Detect a simple liquidity grab based on stop hunt wicks."""
    if len(df) < 5:
        return False
    recent = df.tail(5)
    highest = recent["high"].idxmax()
    lowest = recent["low"].idxmin()
    return highest == recent.index[-1] or lowest == recent.index[-1]


def detect_fvg(df: pd.DataFrame) -> bool:
    """Detect a basic fair value gap using three candles."""
    if len(df) < 3:
        return False
    a, b, c = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    bull_gap = b["low"] > a["high"] and c["low"] > b["high"]
    bear_gap = b["high"] < a["low"] and c["high"] < b["low"]
    return bull_gap or bear_gap


def detect_breaker_block(df: pd.DataFrame) -> bool:
    """Rudimentary breaker block detection."""
    if len(df) < 3:
        return False
    first, mid, last = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    return (
        first["close"] < first["open"]
        and mid["close"] > mid["open"]
        and last["close"] > last["open"]
        and mid["low"] < first["low"]
    )