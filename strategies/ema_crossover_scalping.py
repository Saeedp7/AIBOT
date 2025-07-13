import pandas as pd
from .base import BaseStrategy
from utils.indicators import (
    calculate_ema, calculate_sma, calculate_rsi, calculate_macd,
    calculate_vwap, calculate_bollinger_bands, calculate_adx, calculate_supertrend
)

class EMACrossoverScalpingStrategy(BaseStrategy):
    strategy_type = "scalp"
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 50:
            return

        data.loc[:, 'ema_fast'] = calculate_ema(data['close'], 9)
        data.loc[:, 'ema_slow'] = calculate_ema(data['close'], 21)

        if data['ema_fast'].iloc[-2] < data['ema_slow'].iloc[-2] and data['ema_fast'].iloc[-1] > data['ema_slow'].iloc[-1]:
            self.signal = 'buy'
        elif data['ema_fast'].iloc[-2] > data['ema_slow'].iloc[-2] and data['ema_fast'].iloc[-1] < data['ema_slow'].iloc[-1]:
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
        df = df.copy(deep=True)
        self.analyze(df)
        return self.signal

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        if "atr" in df.columns and not self.is_volatile_enough(df["atr"]):
            self.signal = None
            return None
        self.analyze(df)
        self._log_context(df, pattern_detected="EMACrossover")