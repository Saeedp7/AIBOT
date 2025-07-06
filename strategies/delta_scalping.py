# ⛔ No indicators required – this strategy uses raw price-action triggers only.
import pandas as pd
from .base import BaseStrategy
from utils.indicators import (
    calculate_ema, calculate_sma, calculate_rsi, calculate_macd,
    calculate_vwap, calculate_bollinger_bands, calculate_adx, calculate_supertrend
)

class DeltaDivergenceScalpingStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 10 or 'volume' not in data.columns:
            return

        data['rsi_14'] = calculate_rsi(data['close'], 14)
        data['vwap'] = calculate_vwap(data)

        # Simulate: Price down + volume up => potential reversal
        if data['close'].iloc[-1] < data['close'].iloc[-2] and data['volume'].iloc[-1] > data['volume'].iloc[-2]:
            self.signal = 'buy'
        elif data['close'].iloc[-1] > data['close'].iloc[-2] and data['volume'].iloc[-1] > data['volume'].iloc[-2]:
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'

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
        self._log_context(df, pattern_detected="DeltaScalping")
        return self.signal