import pandas as pd
import numpy as np
from ai_engine.strategy_config import SYMBOL_TOLERANCE_PIPS


def detect_support_resistance_levels(df: pd.DataFrame, window: int = 20, tolerance: float = 0.001):
    support = []
    resistance = []

    for i in range(window, len(df) - window):
        is_support = df['low'].iloc[i] == min(df['low'].iloc[i - window:i + window])
        is_resistance = df['high'].iloc[i] == max(df['high'].iloc[i - window:i + window])

        if is_support:
            level = df['low'].iloc[i]
            if not any(abs(level - s) < tolerance * level for s in support):
                support.append(level)

        if is_resistance:
            level = df['high'].iloc[i]
            if not any(abs(level - r) < tolerance * level for r in resistance):
                resistance.append(level)

    return sorted(support), sorted(resistance)

def detect_recent_price_zone(df: pd.DataFrame, lookback: int = 20):
    recent_high = df['high'].iloc[-lookback:].max()
    recent_low = df['low'].iloc[-lookback:].min()
    mid_point = (recent_high + recent_low) / 2

    return {
        "high": recent_high,
        "low": recent_low,
        "mid": mid_point,
        "range": recent_high - recent_low
    }

def is_price_near_level(price, levels, symbol, sr_sensitivity):
    if sr_sensitivity == "none":
        return False
    elif sr_sensitivity == "low":
        tolerance = SYMBOL_TOLERANCE_PIPS.get(symbol, 10) * 0.5
    elif sr_sensitivity == "high":
        tolerance = SYMBOL_TOLERANCE_PIPS.get(symbol, 10)
    else:
        tolerance = 10  # fallback

    return any(abs(price - level) <= tolerance for level in levels)

