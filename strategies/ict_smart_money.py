import pandas as pd
from .base import BaseStrategy
from core.ict_utils import (
    detect_liquidity_grab,
    detect_fvg,
    detect_breaker_block,
)


class ICTSmartMoneyStrategy(BaseStrategy):
    """Strategy leveraging ICT style concepts."""

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        if len(df) < 5:
            self._log_context(df, pattern_detected="ICTSmartMoney")
            return None
        self._log_context(df, pattern_detected="ICTSmartMoney")
        if detect_liquidity_grab(df) and detect_breaker_block(df):
            self._log_context(df, pattern_detected="ICTSmartMoney", entry_zone="Breaker")
            return "buy" if df["close"].iloc[-1] > df["open"].iloc[-1] else "sell"
        if detect_fvg(df):
            self._log_context(df, pattern_detected="ICTSmartMoney", entry_zone="FVG")
            return "buy" if df["close"].iloc[-1] > df["open"].iloc[-1] else "sell"
        return None
    def check_signal(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        regime: str,
    ) -> str | None:
        import logging

        self.logger = logging.getLogger(__name__)
        self.logger.debug(
            f"[{self.__class__.__name__}] Checking {symbol} {timeframe} in {regime} regime"
        )
        return self.generate_signal(df)