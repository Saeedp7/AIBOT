import pandas as pd
from utils.indicators import calculate_supertrend, calculate_adx, calculate_multi_rsi
from .base import BaseStrategy

class SupertrendADXRSIStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data: pd.DataFrame):
        self.signal = None
        if len(data) < 30:
            return

        supertrend_dir = calculate_supertrend(data, period=10, multiplier=3.0)
        adx_series = calculate_adx(data, di_length=7, adx_smoothing=7)
        rsi_dict = calculate_multi_rsi(data['close'], [3, 21, 28])

        st_now = supertrend_dir.iloc[-1]
        st_prev = supertrend_dir.iloc[-2]
        adx_now = adx_series.iloc[-1]
        rsi_3 = rsi_dict['rsi_3'].iloc[-1]
        rsi_21 = rsi_dict['rsi_21'].iloc[-1]
        rsi_28 = rsi_dict['rsi_28'].iloc[-1]

        if (
            st_prev == -1 and st_now == 1
            and rsi_21 < 66
            and rsi_3 > 80
            and rsi_28 > 49
            and adx_now > 20
        ):
            self.signal = 'buy'
        elif st_prev == 1 and st_now == -1:
            self.signal = 'sell'

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

