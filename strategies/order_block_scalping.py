import pandas as pd

class OrderBlockScalpingStrategy:
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 20:
            return

        # Simulate basic OB logic: buy if strong bullish engulfing after support
        recent = data.iloc[-3:]
        if recent['close'].iloc[-1] > recent['open'].iloc[-1] and recent['close'].iloc[-1] > recent['high'].iloc[-2]:
            self.signal = 'buy'
        elif recent['close'].iloc[-1] < recent['open'].iloc[-1] and recent['close'].iloc[-1] < recent['low'].iloc[-2]:
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'