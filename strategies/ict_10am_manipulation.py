from __future__ import annotations

# ⛔ No indicators required – this strategy uses raw price-action triggers only.
from datetime import time
import pandas as pd

from .base import BaseStrategy
from config.settings import MIN_VOLATILITY_PCT
from strategy_components.liquidity_engine import detect_liquidity_sweep
from strategy_components.smc_engine import detect_fvg_zones, find_order_blocks
from utils.indicators import (
    calculate_ema, calculate_sma, calculate_rsi, calculate_macd,
    calculate_vwap, calculate_bollinger_bands, calculate_adx, calculate_supertrend
)


class ICT10AMManipulationStrategy(BaseStrategy):
    """ICT 10AM liquidity manipulation entry."""

    strategy_group = "day"
    strategy_type = "scalp"

    def _confirm_ltf_entry(self, ltf_df: pd.DataFrame | None, direction: str) -> bool:
        """Confirm entry on a lower timeframe via engulfing or BOS."""
        if ltf_df is None or len(ltf_df) < 2:
            return False

        last = ltf_df.iloc[-1]
        prev = ltf_df.iloc[-2]

        bullish_engulf = (
            last["close"] > last["open"]
            and prev["close"] < prev["open"]
            and last["close"] >= prev["open"]
            and last["open"] <= prev["close"]
        )
        bearish_engulf = (
            last["close"] < last["open"]
            and prev["close"] > prev["open"]
            and last["open"] >= prev["close"]
            and last["close"] <= prev["open"]
        )

        lookback = 3
        bos_up = last["high"] > ltf_df["high"].iloc[-(lookback + 1) : -1].max() and last["close"] > last["open"]
        bos_down = last["low"] < ltf_df["low"].iloc[-(lookback + 1) : -1].min() and last["close"] < last["open"]

        if direction == "buy":
            return bullish_engulf or bos_up
        else:
            return bearish_engulf or bos_down

    def generate_signal(
        self,
        df: pd.DataFrame,
        context: dict | None = None,
        *,
        ltf_df: pd.DataFrame | None = None,
    ) -> dict | None:
        if df is None or df.empty:
            return None

        df['ema_20'] = calculate_ema(df['close'], 20)
        df['vwap'] = calculate_vwap(df)

        ts = df.index[-1].to_pydatetime()
        if ts.time() != time(10, 0):
            return None

        bias = context.get("bias") if context else None
        if bias not in ("bullish", "bearish"):
            self._log_context(df, pattern_detected="ICT10AM")
            return None

        if not detect_liquidity_sweep(df):
            return None

        fvgs = detect_fvg_zones(df)
        obs = find_order_blocks(df)
        zone = fvgs[-1] if fvgs else (obs[-1] if obs else None)
        if zone is None:
            return None

        last = df.iloc[-1]
        body = abs(last["close"] - last["open"])
        wick = last["high"] - last["low"]
        if body <= wick:
            return None

        candle_range_pct = wick / last["close"]
        if candle_range_pct < MIN_VOLATILITY_PCT:
            return None

        direction = "buy" if bias == "bullish" else "sell"
        if zone.get("type") == "bearish":
            direction = "sell"
        elif zone.get("type") == "bullish":
            direction = "buy"

        upper_wick = last["high"] - max(last["open"], last["close"])
        lower_wick = min(last["open"], last["close"]) - last["low"]
        if direction == "buy" and lower_wick < body * 1.5:
            return None
        if direction == "sell" and upper_wick < body * 1.5:
            return None

        if not self._confirm_ltf_entry(ltf_df, direction):
            return None

        sl = last["low"] if direction == "buy" else last["high"]
        entry = last["close"]
        risk = abs(entry - sl)
        tp = entry + 3 * risk if direction == "buy" else entry - 3 * risk

        self._log_context(df, pattern_detected="ICT10AM", entry_zone=zone.get("type"), bias=bias)
        return {
            "direction": direction,
            "sl": float(sl),
            "tp1": float(tp),
            "label": "ICT10AM",
            "regime": bias,
        }

    def check_signal(self, symbol: str, timeframe: str, df: pd.DataFrame, regime: str) -> str | None:
        signal = self.generate_signal(df, context={"bias": regime})
        if isinstance(signal, dict):
            return signal.get("direction")
        return None