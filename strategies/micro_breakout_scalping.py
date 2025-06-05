import pandas_ta as ta

class MicroBreakoutScalpingStrategy:
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 25:
            return

        recent_high = data['high'].iloc[-10:-1].max()
        recent_low = data['low'].iloc[-10:-1].min()
        last_close = data['close'].iloc[-1]

        if last_close > recent_high:
            self.signal = 'buy'
        elif last_close < recent_low:
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'