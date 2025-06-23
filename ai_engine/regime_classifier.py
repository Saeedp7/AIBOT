import pandas as pd

from config.manager import get_config
from utils.indicators import calculate_ema, calculate_atr
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
        atr_slope_threshold = float(get_config("REGIME_ATR_SLOPE_THRESHOLD", 0.7))
    if ema_slope_threshold is None:
        ema_slope_threshold = float(
            get_config("REGIME_EMA_DISTANCE_THRESHOLD", 0.5)
        )

    ema = df["ema_50"] if "ema_50" in df.columns else calculate_ema(df["close"], 50)
    atr = calculate_atr(df, period=14)

    ema_slope = (ema.iloc[-1] - ema.iloc[-window]) / max(ema.iloc[-window], 1e-8) * 100
    atr_slope = (atr.iloc[-1] - atr.iloc[-window]) / max(atr.iloc[-window], 1e-8) * 100

    highs = df["high"].iloc[-window:]
    lows = df["low"].iloc[-window:]

    high_trend = (highs.diff() > 0).mean()
    low_trend = (lows.diff() > 0).mean()

    if high_trend > 0.6 and low_trend > 0.6:
        structure = "HH/HL"
    elif high_trend < 0.4 and low_trend < 0.4:
        structure = "LL/LH"
    else:
        structure = "range"

    if abs(ema_slope) > ema_slope_threshold and structure != "range":
        regime = "trending"
    elif atr_slope > atr_slope_threshold:
        regime = "volatile"
    else:
       regime = "ranging"

    print(
        f"[REGIME] EMA Slope: {ema_slope:.2f} | ATR Change: {atr_slope:.2f} | Structure: {structure} → Regime: {regime}"
    )
    logger.info(
        "[REGIME] EMA %.2f→%.2f (%.2f%%) | ATR %.5f→%.5f (%.2f%%) | %s → %s",
        ema.iloc[-window],
        ema.iloc[-1],
        ema_slope,
        atr.iloc[-window],
        atr.iloc[-1],
        atr_slope,
        structure,
        regime,
    )
    return regime