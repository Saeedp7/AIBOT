from __future__ import annotations

from datetime import time
import pandas as pd

from .base import BaseStrategy
from strategy_components.liquidity_engine import detect_liquidity_sweep
from strategy_components.smc_engine import detect_fvg_zones, find_order_blocks


class ICT10AMManipulationStrategy(BaseStrategy):
    """ICT 10AM liquidity manipulation entry."""

    strategy_group = "day"

    def generate_signal(self, df: pd.DataFrame, context: dict | None = None) -> dict | None:
        if df is None or df.empty:
            return None

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

        direction = "buy" if bias == "bullish" else "sell"
        if zone.get("type") == "bearish":
            direction = "sell"
        elif zone.get("type") == "bullish":
            direction = "buy"

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