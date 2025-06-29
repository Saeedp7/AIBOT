# strategies/trend_following.py

import pandas as pd
from utils.indicators import calculate_sma
from .base import BaseStrategy

class TrendFollowingStrategy(BaseStrategy):
    def __init__(self, fast_period=10, slow_period=30):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.last_signal = None  # "buy" or "sell"

    def analyze(self, data: pd.DataFrame):
        """Analyze market and set last signal."""
        if len(data) < max(self.fast_period, self.slow_period):
            self.last_signal = None
            return
        data = data.copy()  # FULLY copy first

        data.loc[:, 'fast_ma'] = calculate_sma(data['close'], self.fast_period)
        data.loc[:, 'slow_ma'] = calculate_sma(data['close'], self.slow_period)

        if data['fast_ma'].iloc[-2] < data['slow_ma'].iloc[-2] and data['fast_ma'].iloc[-1] > data['slow_ma'].iloc[-1]:
            self.last_signal = "buy"
        elif data['fast_ma'].iloc[-2] > data['slow_ma'].iloc[-2] and data['fast_ma'].iloc[-1] < data['slow_ma'].iloc[-1]:
            self.last_signal = "sell"
        else:
            self.last_signal = None


    def should_buy(self):
        return self.last_signal == "buy"

    def should_sell(self):
        return self.last_signal == "sell"

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
        return self.last_signal

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        self._log_context(df, pattern_detected="TrendFollowing")
        return self.last_signal