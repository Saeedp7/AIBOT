import pandas as pd
from .base import BaseStrategy
from utils.indicators import calculate_ema
from core.price_action import is_bullish_engulfing, is_bearish_engulfing

class OrderBlockScalpingStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 20:
            return

        # Simulate basic OB logic: buy if strong bullish engulfing after support
        ema20 = calculate_ema(data["close"], 20).iloc[-1]
        last_close = data["close"].iloc[-1]

        if is_bullish_engulfing(data.tail(2)) and last_close > ema20:
            self.signal = "buy"
        elif is_bearish_engulfing(data.tail(2)) and last_close < ema20:
            self.signal = "sell"

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