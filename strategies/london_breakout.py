import pandas as pd
from .base import BaseStrategy

class LondonBreakoutStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 40:
            return

        breakout_high = data['high'].iloc[-30:-10].max()
        breakout_low = data['low'].iloc[-30:-10].min()

        if data['close'].iloc[-1] > breakout_high:
            self.signal = 'buy'
        elif data['close'].iloc[-1] < breakout_low:
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
        import logging

        self.logger = logging.getLogger(__name__)
        self.logger.debug(
            f"[{self.__class__.__name__}] Checking {symbol} {timeframe} in {regime} regime"
        )
        self.analyze(df)
        return self.signal

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        self._log_context(df, pattern_detected="LondonBreakout")
        return self.signal