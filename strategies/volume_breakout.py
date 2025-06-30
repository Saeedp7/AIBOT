import pandas as pd
from .base import BaseStrategy

class VolumeBreakoutStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 30 or 'volume' not in data.columns:
            return

        avg_volume = data['volume'].rolling(20).mean().iloc[-1]
        if data['volume'].iloc[-1] > 1.5 * avg_volume:
            if data['close'].iloc[-1] > data['high'].iloc[-5:-1].max():
                self.signal = 'buy'
            elif data['close'].iloc[-1] < data['low'].iloc[-5:-1].min():
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
        self._log_context(df, pattern_detected="VolumeBreakout")
        return self.signal