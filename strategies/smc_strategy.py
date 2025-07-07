from __future__ import annotations

"""Simplified Smart Money Concept based strategy."""

from typing import Dict
import pandas as pd

from .base import BaseStrategy
from strategy_components.market_structure import detect_bos_mss
from strategy_components.liquidity_engine import (
    identify_liquidity_zones,
    detect_fvgs,
    detect_stop_runs,
)
from strategy_components.smc_engine import detect_order_blocks
from strategy_components.pattern_detector import detect_po3
from strategy_components.bias_framework import (
    determine_daily_bias,
    align_with_institutional_flow,
)
from utils.indicators import (
    calculate_ema, calculate_sma, calculate_rsi, calculate_macd,
    calculate_vwap, calculate_bollinger_bands, calculate_adx, calculate_supertrend
)
from strategy_components.session_filter import in_killzone


class SMCStrategy(BaseStrategy):
    """Unifies basic SMC concepts for trade generation."""

    strategy_group = "day"
    strategy_type = "day"

    def generate_signal(self, df: pd.DataFrame) -> Dict | None:
        if "atr" in df.columns and not self.is_volatile_enough(df["atr"]):
            return None
        if df is None or df.empty:
            return None
        df['sma_20'] = calculate_sma(df['close'], 20)
        df['rsi_14'] = calculate_rsi(df['close'], 14)
        df['vwap'] = calculate_vwap(df)
        if not in_killzone(df.index[-1].to_pydatetime()):
            return None
        self._log_context(df, pattern_detected="SMC", entry_zone="OB")
        ms = detect_bos_mss(df)
        if not ms["bos"]:
            return None
        bias = determine_daily_bias(df)
        flow = align_with_institutional_flow(df)
        direction = ms["bos"]
        if bias != direction and flow != direction:
            return None
        ob_list = detect_order_blocks(df)
        if not ob_list:
            return None
        ob = ob_list[-1]
        liq = identify_liquidity_zones(df)
        fvgs = [f for f in detect_fvgs(df) if f.get("type") == direction]
        tp1 = fvgs[-1]["high"] if fvgs else df["close"].iloc[-1] + 0.5
        tp2 = liq.get("eqh") if direction == "bullish" else liq.get("eql")
        tp3 = liq.get("pdh") if direction == "bullish" else liq.get("pdl")
        entry = (
            ob.get("high") if direction == "bearish" else ob.get("low")
        )
        if fvgs:
            last_gap = fvgs[-1]
            entry = (last_gap["low"] + last_gap["high"]) / 2
        if entry is None:
            entry = df["close"].iloc[-1]
        sl = ob.get("low") if direction == "bullish" else ob.get("high")
        if sl and abs(entry - sl) > 1e-5:
            rr_ratio = abs((tp1 - entry) / (entry - sl))
        else:
            rr_ratio = 0.0
        label = "SMC-PO3" if detect_po3(df) else "SMC"
        return {
            "entry": float(entry),
            "sl": float(sl),
            "tp1": float(tp1) if tp1 else None,
            "tp2": float(tp2) if tp2 else None,
            "tp3": float(tp3) if tp3 else None,
            "direction": direction,
            "label": label,
            "regime": bias,
            "rr_ratio": rr_ratio,
        }

    def check_signal(self, symbol: str, timeframe: str, df: pd.DataFrame, regime: str) -> str | None:
        if "atr" in df.columns and not self.is_volatile_enough(df["atr"]):
            return None
        trade = self.generate_signal(df)
        if trade:
            return trade.get("direction")
        return None