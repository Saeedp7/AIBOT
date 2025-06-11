import pandas as pd
from .base import BaseStrategy

class DeltaDivergenceScalpingStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 10 or 'volume' not in data.columns:
            return

        # Simulate: Price down + volume up => potential reversal
        if data['close'].iloc[-1] < data['close'].iloc[-2] and data['volume'].iloc[-1] > data['volume'].iloc[-2]:
            self.signal = 'buy'
        elif data['close'].iloc[-1] > data['close'].iloc[-2] and data['volume'].iloc[-1] > data['volume'].iloc[-2]:
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