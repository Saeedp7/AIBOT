import pandas as pd
from utils.indicators import calculate_ema
from .base import BaseStrategy

class VolumeBreakoutStrategy(BaseStrategy):
    def __init__(self):
        self.signal = None

    def analyze(self, data):
        self.signal = None
        if len(data) < 30 or 'volume' not in data.columns:
            return

        data = data.copy()
        data['ema_volume'] = calculate_ema(data['volume'], 20)
        latest = data.iloc[-1]

        if latest['volume'] > 1.5 * latest['ema_volume']:
            if latest['close'] > data['high'].rolling(20).max().iloc[-1]:
                self.signal = 'buy'
            elif latest['close'] < data['low'].rolling(20).min().iloc[-1]:
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
            return None
        df = df.copy()
        df["ema_volume"] = calculate_ema(df["volume"], 20)
        latest = df.iloc[-1]

        if latest["volume"] > 1.5 * latest["ema_volume"]:
            if latest["close"] > df["high"].rolling(20).max().iloc[-1]:
                signal = "buy"
            elif latest["close"] < df["low"].rolling(20).min().iloc[-1]:
                signal = "sell"
            else:
                signal = None
        else:
            signal = None
        if signal:
            self._log_context(df, pattern_detected="VolumeBreakout")
        return signal
