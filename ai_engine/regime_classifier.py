import pandas as pd

from config.manager import get_config
from utils.indicators import calculate_ema, calculate_atr


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
    ema_slope = (ema.iloc[-1] - ema.iloc[-window]) / df["close"].iloc[-window]
    atr_slope = (atr.iloc[-1] - atr.iloc[-window]) / atr.iloc[-window]

    highs = df["high"].iloc[-window:]
    lows = df["low"].iloc[-window:]
    if highs.is_monotonic_increasing and lows.is_monotonic_increasing:
        structure = "HH/HL"
    elif highs.is_monotonic_decreasing and lows.is_monotonic_decreasing:
        structure = "LL/LH"
    else:
        structure = "range"

    if abs(ema_slope) > ema_slope_threshold:
        regime = "trending"
    elif atr_slope > atr_slope_threshold:
        regime = "volatile"
    else:
       regime = "ranging"

    print(
        f"[REGIME] EMA Slope: {ema_slope:.2f} | ATR Change: {atr_slope:.2f} | Structure: {structure} → Regime: {regime}"
    )
    return regime