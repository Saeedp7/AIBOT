import pandas as pd
from utils.indicators import calculate_rsi, calculate_vwap
from .base import BaseStrategy
from core.ict_utils import detect_liquidity_grab

class VWAPReversionStrategy(BaseStrategy):
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
        data.index = data.index.tz_localize(None)
        data.loc[:, 'vwap'] = calculate_vwap(data)

        last_price = data['close'].iloc[-1]
        vwap_val = data['vwap'].iloc[-1]
        rsi = calculate_rsi(data['close']).iloc[-1]

        if detect_liquidity_grab(data) and last_price < vwap_val and rsi < 45:
            self.signal = 'buy'
        elif detect_liquidity_grab(data) and last_price > vwap_val and rsi > 55:
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
        self._log_context(df, pattern_detected="VWAPReversion", entry_zone="VWAP")
        return self.signal