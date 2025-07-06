import pandas as pd
from utils.indicators import calculate_ema, calculate_rsi
from .base import BaseStrategy

class MeanReversionStrategy(BaseStrategy):
    """Mean reversion strategy using RSI and EMA indicators."""

    def __init__(self) -> None:
        self.signal: str | None = None

    def analyze(self, df: pd.DataFrame) -> None:
        self.signal = None
        if len(df) < 30:
            return

        if "ema_50" not in df.columns:
            df["ema_50"] = calculate_ema(df["close"], 50)
        if "rsi_14" not in df.columns:
            df["rsi_14"] = calculate_rsi(df["close"], 14)

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
        if "atr" in df.columns and not self.is_volatile_enough(df["atr"]):
            self.signal = None
            return None
        import logging

        self.logger = logging.getLogger(__name__)
        self.logger.debug(
            f"[{self.__class__.__name__}] Checking {symbol} {timeframe} in {regime} regime"
        )
        self.analyze(df)
        return self.signal

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        if "atr" in df.columns and not self.is_volatile_enough(df["atr"]):
            self.signal = None
            return None
        self.analyze(df)
        self._log_context(df, pattern_detected="MeanReversion")
        return self.signal