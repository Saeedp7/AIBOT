import pandas as pd

class VolumeBreakoutStrategy:
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

    def check_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        return self.signal