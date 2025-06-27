from __future__ import annotations

"""Higher timeframe bias determination for SMC."""

import pandas as pd
from typing import Tuple


def determine_daily_bias(candles: pd.DataFrame) -> str:
    """Simple bias based on 50-period moving average."""
    if len(candles) < 50:
        return "neutral"
    ma = candles["close"].rolling(50).mean()
    if candles["close"].iloc[-1] > ma.iloc[-1]:
        return "bullish"
    if candles["close"].iloc[-1] < ma.iloc[-1]:
        return "bearish"
    return "neutral"


def is_in_premium_or_discount(current_price: float, fib_swing: Tuple[float, float]) -> str:
    """Return 'premium' if price above 0.5 of fib swing else 'discount'."""
    high, low = fib_swing
    mid = (high + low) / 2
    return "premium" if current_price > mid else "discount"


def align_with_institutional_flow(candles: pd.DataFrame) -> str:
    """Very rough trend direction to mimic institutional flow."""
    if len(candles) < 10:
        return "neutral"
    change = candles["close"].iloc[-1] - candles["close"].iloc[-10]
    if change > 0:
        return "bullish"
    if change < 0:
        return "bearish"
    return "neutral"