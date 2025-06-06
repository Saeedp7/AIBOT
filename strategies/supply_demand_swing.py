import pandas as pd

class SupplyDemandSwingStrategy:
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 40:
            return

        support = data['low'].rolling(20).min()
        resistance = data['high'].rolling(20).max()

        last_close = data['close'].iloc[-1]
        if last_close <= support.iloc[-1] * 1.01:
            self.signal = 'buy'
        elif last_close >= resistance.iloc[-1] * 0.99:
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'

    def check_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        return self.signal