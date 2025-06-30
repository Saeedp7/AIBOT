import pandas as pd
import pandas_ta as ta
from .base import BaseStrategy

class MACrossoverSwingStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 200:
            return

        data.loc[:, 'ma_50'] = ta.sma(data['close'], length=50)
        data.loc[:, 'ma_200'] = ta.sma(data['close'], length=200)

        data = data.dropna(subset=['ma_50', 'ma_200'])
        if len(data) < 2:
            return

        if data['ma_50'].iloc[-2] < data['ma_200'].iloc[-2] and data['ma_50'].iloc[-1] > data['ma_200'].iloc[-1]:
            self.signal = 'buy'
        elif data['ma_50'].iloc[-2] > data['ma_200'].iloc[-2] and data['ma_50'].iloc[-1] < data['ma_200'].iloc[-1]:
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
        self._log_context(df, pattern_detected="MACrossover")
        return self.signal