from __future__ import annotations

"""Reusable price action pattern utilities."""

from typing import Iterable

import pandas as pd


def is_bullish_engulfing(df: pd.DataFrame) -> bool:
    """Return ``True`` if last two candles form a bullish engulfing pattern."""
    if len(df) < 2:
        return False
    prev, curr = df.iloc[-2], df.iloc[-1]
    return (
        prev["close"] < prev["open"]
        and curr["close"] > curr["open"]
        and curr["close"] >= prev["open"]
        and curr["open"] <= prev["close"]
    )


def is_bearish_engulfing(df: pd.DataFrame) -> bool:
    """Return ``True`` if last two candles form a bearish engulfing pattern."""
    if len(df) < 2:
        return False
    prev, curr = df.iloc[-2], df.iloc[-1]
    return (
        prev["close"] > prev["open"]
        and curr["close"] < curr["open"]
        and curr["open"] >= prev["close"]
        and curr["close"] <= prev["open"]
    )


def is_inside_bar(df: pd.DataFrame) -> bool:
    """Return ``True`` if the latest candle is inside the previous candle."""
    if len(df) < 2:
        return False
    prev, curr = df.iloc[-2], df.iloc[-1]
    return curr["high"] <= prev["high"] and curr["low"] >= prev["low"]


def is_pin_bar(df: pd.DataFrame) -> bool:
    """Simple pin bar detection based on wick size."""
    if len(df) < 1:
        return False
    c = df.iloc[-1]
    body = abs(c["close"] - c["open"])
    upper_wick = c["high"] - max(c["close"], c["open"])
    lower_wick = min(c["close"], c["open"]) - c["low"]
    return upper_wick >= body * 2 or lower_wick >= body * 2