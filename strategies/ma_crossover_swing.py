import pandas as pd
import pandas_ta as ta
from .base import BaseStrategy

class MACrossoverSwingStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 200:
            return

        data.loc[:, 'ma_50'] = ta.sma(data['close'], length=50)
        data.loc[:, 'ma_200'] = ta.sma(data['close'], length=200)

        data = data.dropna(subset=['ma_50', 'ma_200'])
        if len(data) < 2:
            return

        if data['ma_50'].iloc[-2] < data['ma_200'].iloc[-2] and data['ma_50'].iloc[-1] > data['ma_200'].iloc[-1]:
            self.signal = 'buy'
        elif data['ma_50'].iloc[-2] > data['ma_200'].iloc[-2] and data['ma_50'].iloc[-1] < data['ma_200'].iloc[-1]:
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'

    def check_signal(self, df: pd.DataFrame) -> str | None:
        df = df.copy(deep=True)
        self.analyze(df)
        return self.signal

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        return self.signal