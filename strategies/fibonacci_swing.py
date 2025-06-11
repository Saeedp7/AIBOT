import pandas as pd
import numpy as np
from .base import BaseStrategy

class FibonacciSwingStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 100:
            return

        recent = data[-50:]
        high = recent['high'].max()
        low = recent['low'].min()
        close = recent['close'].iloc[-1]

        retracement_618 = high - (high - low) * 0.618

        if close < retracement_618 * 1.01:
            self.signal = 'buy'
        elif close > retracement_618 * 0.99:
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'

    def check_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        return self.signal

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        return self.signal