import pandas as pd
from .base import BaseStrategy
from utils.indicators import calculate_rsi
from core.price_action import (
    is_bullish_engulfing,
    is_bearish_engulfing,
    is_inside_bar,
    is_pin_bar,
)


class PriceActionStrategy(BaseStrategy):
    """Basic strategy using price action utilities."""

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        if len(df) < 5:
            return None
        recent = df.tail(2)
        rsi = calculate_rsi(df["close"]).iloc[-1]

        if (is_bullish_engulfing(recent) or is_pin_bar(recent)) and rsi < 70:
            return "buy"
        if (is_bearish_engulfing(recent) or is_pin_bar(recent)) and rsi > 30:
            return "sell"
        if is_inside_bar(recent):
            return None
        return None
    def check_signal(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        regime: str,
    ) -> str | None:
        import logging

        self.logger = logging.getLogger(__name__)
        self.logger.debug(
            f"[{self.__class__.__name__}] Checking {symbol} {timeframe} in {regime} regime"
        )
        return self.generate_signal(df)