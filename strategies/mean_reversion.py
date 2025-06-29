import pandas as pd
from .base import BaseStrategy

class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy using RSI and EMA indicators."""

    def __init__(self) -> None:
        self.signal: str | None = None

    def analyze(self, df: pd.DataFrame) -> None:
        self.signal = None
        if len(df) < 30:
            return

        required = {"ema_50", "rsi_14"}
        if not required.issubset(df.columns):
            return

        close = df["close"].iloc[-1]
        ema = df["ema_50"].iloc[-1]
        rsi = df["rsi_14"].iloc[-1]

        if rsi < 30 and close < ema * 0.98:
            self.signal = "buy"
        elif rsi > 70 and close > ema * 1.02:
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
        self._log_context(df, pattern_detected="MeanReversion")
        return self.signal