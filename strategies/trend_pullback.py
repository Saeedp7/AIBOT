import pandas as pd
import pandas_ta as ta

class TrendPullbackStrategy:
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 50:
            return

        data.loc[:, 'ema_20'] = ta.ema(data['close'], length=20)
        data.loc[:, 'ema_50'] = ta.ema(data['close'], length=50)

        if data['ema_20'].iloc[-1] > data['ema_50'].iloc[-1] and data['close'].iloc[-1] < data['ema_20'].iloc[-1]:
            self.signal = 'buy'
        elif data['ema_20'].iloc[-1] < data['ema_50'].iloc[-1] and data['close'].iloc[-1] > data['ema_20'].iloc[-1]:
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'

    def check_signal(self, df: pd.DataFrame) -> str | None:
        df = df.copy(deep=True)
        self.analyze(df)
        return self.signal