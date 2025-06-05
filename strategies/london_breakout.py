class LondonBreakoutStrategy:
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