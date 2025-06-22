import pandas as pd
from .base import BaseStrategy
from core.ict_utils import (
    detect_liquidity_grab,
    detect_fvg,
    detect_breaker_block,
)


class ICTSmartMoneyStrategy(BaseStrategy):
    """Strategy leveraging ICT style concepts."""

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        if len(df) < 5:
            return None
        if detect_liquidity_grab(df) and detect_breaker_block(df):
            return "buy" if df["close"].iloc[-1] > df["open"].iloc[-1] else "sell"
        if detect_fvg(df):
            return "buy" if df["close"].iloc[-1] > df["open"].iloc[-1] else "sell"
        return None
