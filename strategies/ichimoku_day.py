import pandas as pd
from .base import BaseStrategy
from utils.indicators import (
    calculate_ema, calculate_sma, calculate_rsi, calculate_macd,
    calculate_vwap, calculate_bollinger_bands, calculate_adx, calculate_supertrend
)

class IchimokuDayStrategy(BaseStrategy):
    strategy_type = "day"

    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 80:
            return

        data = data.copy()

        if 'time' in data.columns:
            data.index = pd.to_datetime(data['time'])

        data = data.sort_index()
        data['ema_20'] = calculate_ema(data['close'], 20)

        # Get Ichimoku components
        conv_base, cloud = ta.ichimoku(
            high=data['high'], low=data['low'], close=data['close'], offset=0
        )

        if conv_base is None or cloud is None:
            return

        for df in [conv_base, cloud]:
            if df is not None:
                for col in df.columns:
                    if col not in data.columns:
                        data.loc[:, col] = df[col]

        required = ['ITS_9', 'KJS_26', 'SSA_9_26_52', 'SSB_9_26_52']
        if not all(col in data.columns for col in required):
            return

        latest = data.iloc[-1]

        if (
            latest['ITS_9'] > latest['KJS_26']
            and latest['close'] > max(latest['SSA_9_26_52'], latest['SSB_9_26_52'])
        ):
            self.signal = 'buy'
        elif (
            latest['ITS_9'] < latest['KJS_26']
            and latest['close'] < min(latest['SSA_9_26_52'], latest['SSB_9_26_52'])
        ):
            self.signal = 'sell'

    def should_buy(self):
        return self.signal == 'buy'

    def should_sell(self):
        return self.signal == 'sell'

    def check_signal(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        regime: str,
    ) -> str | None:
        if "atr" in df.columns and not self.is_volatile_enough(df["atr"]):
            self.signal = None
            return None
        import logging

        self.logger = logging.getLogger(__name__)
        self.logger.debug(
            f"[{self.__class__.__name__}] Checking {symbol} {timeframe} in {regime} regime"
        )
        self.analyze(df)
        return self.signal

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        if "atr" in df.columns and not self.is_volatile_enough(df["atr"]):
            self.signal = None
            return None
        self.analyze(df)
        self._log_context(df, pattern_detected="IchimokuDay")
        return self.signal