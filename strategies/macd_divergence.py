import pandas as pd
from utils.indicators import calculate_macd
from .base import BaseStrategy

class MACDDivergenceStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 35:
            return

        macd_line, signal_line, _ = calculate_macd(data['close'])
        data.loc[:, 'macd'] = macd_line
        data.loc[:, 'macd_signal'] = signal_line

        if data['macd'].iloc[-2] < data['macd_signal'].iloc[-2] and data['macd'].iloc[-1] > data['macd_signal'].iloc[-1]:
            self.signal = 'buy'
        elif data['macd'].iloc[-2] > data['macd_signal'].iloc[-2] and data['macd'].iloc[-1] < data['macd_signal'].iloc[-1]:
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
        self._log_context(df, pattern_detected="MACDDivergence")
        return self.signal