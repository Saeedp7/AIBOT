import pandas as pd
from .base import BaseStrategy

class BreakoutStrategy(BaseStrategy):
    """Simple breakout strategy using pre-computed indicator columns."""

    def __init__(self, lookback: int = 20) -> None:
        self.lookback = lookback
        self.signal: str | None = None

    def analyze(self, df: pd.DataFrame) -> None:
        """Calculate the breakout signal and store it in ``self.signal``."""
        self.signal = None
        if len(df) < self.lookback + 1:
            return

        required = {"ema_14", "ema_50", "rsi_14"}
        if not required.issubset(df.columns):
            return

        high_level = df["high"].iloc[-self.lookback:-1].max()
        low_level = df["low"].iloc[-self.lookback:-1].min()

        close = df["close"].iloc[-1]
        ema_fast = df["ema_14"].iloc[-1]
        ema_slow = df["ema_50"].iloc[-1]
        rsi = df["rsi_14"].iloc[-1]

        if close > high_level and ema_fast > ema_slow and rsi > 60:
            self.signal = "buy"
        elif close < low_level and ema_fast < ema_slow and rsi < 40:
            self.signal = "sell"

    def should_buy(self) -> bool:
        return self.signal == "buy"

    def should_sell(self) -> bool:
        return self.signal == "sell"

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
        self.analyze(df)
        return self.signal

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        return self.signal