import pandas as pd
import pandas_ta as ta

class EMACrossoverScalpingStrategy:
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 50:
            return

        data.loc[:, 'ema_fast'] = ta.ema(data['close'], length=9)
        data.loc[:, 'ema_slow'] = ta.ema(data['close'], length=21)

        if data['ema_fast'].iloc[-2] < data['ema_slow'].iloc[-2] and data['ema_fast'].iloc[-1] > data['ema_slow'].iloc[-1]:
            self.signal = 'buy'
        elif data['ema_fast'].iloc[-2] > data['ema_slow'].iloc[-2] and data['ema_fast'].iloc[-1] < data['ema_slow'].iloc[-1]:
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'

    def check_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        return self.signal