from __future__ import annotations

"""Order block detection utilities."""

from typing import List, Dict
import pandas as pd
from .liquidity_engine import detect_fvgs

def detect_order_blocks(candles: pd.DataFrame, lookback: int = 5) -> List[Dict[str, float]]:
    """Identify simple bullish/bearish order blocks."""
    blocks: List[Dict[str, float]] = []
    if len(candles) < lookback + 2:
        return blocks
    for i in range(len(candles) - lookback - 1, len(candles) - 1):
        curr = candles.iloc[i]
        nxt = candles.iloc[i + 1]
        body = curr["close"] - curr["open"]
        if body > 0 and nxt["low"] <= curr["low"]:
            blocks.append({"index": i, "type": "bullish", "low": curr["low"], "high": curr["high"]})
        elif body < 0 and nxt["high"] >= curr["high"]:
            blocks.append({"index": i, "type": "bearish", "high": curr["high"], "low": curr["low"]})
    return blocks


def detect_mitigation_blocks(candles: pd.DataFrame) -> List[int]:
    """Placeholder for mitigation block detection."""
    if len(candles) < 3:
        return []
    mids = []
    for i in range(2, len(candles)):
        if candles["close"].iloc[i] > candles["open"].iloc[i - 1] < candles["close"].iloc[i - 1]:
            mids.append(i)
    return mids


def validate_ob_with_volume(candles: pd.DataFrame, ob: Dict[str, float]) -> bool:
    """Confirm OB with volume spike compared to previous candle."""
    idx = ob.get("index")
    if idx is None or "volume" not in candles.columns or idx == 0:
        return True
    return candles["volume"].iloc[idx] > candles["volume"].iloc[idx - 1]

def detect_fvg_zones(candles: pd.DataFrame) -> List[Dict[str, float]]:
    """Wrapper around ``detect_fvgs`` for naming consistency."""
    return detect_fvgs(candles)


def find_order_blocks(candles: pd.DataFrame, lookback: int = 5) -> List[Dict[str, float]]:
    """Alias for ``detect_order_blocks`` with default lookback."""
    return detect_order_blocks(candles, lookback=lookback)