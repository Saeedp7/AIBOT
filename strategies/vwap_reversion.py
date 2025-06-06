import pandas as pd
import pandas_ta as ta

class VWAPReversionStrategy:
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 30 or 'volume' not in data.columns:
            return

        data = data.copy()
        if 'time' in data.columns:
            data.index = pd.to_datetime(data['time'])
        data = data.sort_index()

        # Calculate VWAP
        data['vwap'] = ta.vwap(high=data['high'], low=data['low'], close=data['close'], volume=data['volume'])

        last_price = data['close'].iloc[-1]
        vwap_val = data['vwap'].iloc[-1]

        if last_price < vwap_val * 0.995:
            self.signal = 'buy'
        elif last_price > vwap_val * 1.005:
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'

    def check_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        return self.signal