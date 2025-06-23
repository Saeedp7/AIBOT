import pandas as pd

from config.settings import EMA_SLOPE_THRESHOLD, ATR_VOLATILITY_THRESHOLD
from utils.indicators import calculate_ema, calculate_atr
from utils.structure_detection import (
    is_higher_highs_last_n,
    is_lower_lows_last_n,
)
import logging

logger = logging.getLogger(__name__)

def detect_market_regime(
    df: pd.DataFrame,
    window: int = 20,
    atr_slope_threshold: float | None = None,
    ema_slope_threshold: float | None = None,
) -> str:
    """Return market regime based on EMA and ATR slope analysis."""

    if len(df) < window + 50:
        return "unknown"
    if atr_slope_threshold is None:
        atr_slope_threshold = ATR_VOLATILITY_THRESHOLD
    if ema_slope_threshold is None:
        ema_slope_threshold = EMA_SLOPE_THRESHOLD

    ema = df["ema_50"] if "ema_50" in df.columns else calculate_ema(df["close"], 50)
    atr = calculate_atr(df, period=14)

    ema_start = ema.iloc[-window]
    ema_end = ema.iloc[-1]
    ema_slope = (ema_end - ema_start) / max(ema_start, 1e-8) * 100

    atr_start = atr.iloc[-window]
    atr_end = atr.iloc[-1]
    atr_change = (atr_end - atr_start) / max(atr_start, 1e-8) * 100

    if ema_slope > ema_slope_threshold and is_higher_highs_last_n(df):
        structure = "uptrend"
    elif ema_slope < -ema_slope_threshold and is_lower_lows_last_n(df):
        structure = "downtrend"
    else:
        structure = "range"

    if abs(ema_slope) > ema_slope_threshold and structure in {"uptrend", "downtrend"}:
        regime = "trending"
    elif abs(atr_change) > atr_slope_threshold:
        regime = "volatile"
    else:
       regime = "ranging"

    logger.info(
        f"[REGIME] EMA {ema_start:.2f}→{ema_end:.2f} ({ema_slope:+.2f}%) | "
        f"ATR {atr_start:.5f}→{atr_end:.5f} ({atr_change:+.2f}%) | "
        f"Structure: {structure} → Regime: {regime}"
    )
    return regime