import pandas as pd
from utils.indicators import calculate_atr
from ai_engine.regime_classifier import detect_market_regime
from .base import BaseStrategy


def is_trend_continuation(df: pd.DataFrame, regime: str, lookback: int = 10) -> bool:
    """Return True if price breaks out after a pullback in the trend direction."""
    if regime == "uptrend":
        return (
            df["low"].iloc[-lookback:-3].min() < df["low"].iloc[-lookback]
            and df["close"].iloc[-1] > df["high"].iloc[-lookback:-3].max()
        )
    if regime == "downtrend":
        return (
            df["high"].iloc[-lookback:-3].max() > df["high"].iloc[-lookback]
            and df["close"].iloc[-1] < df["low"].iloc[-lookback:-3].min()
        )
    return False


def add_bollinger_bands(df: pd.DataFrame, period: int = 20, stddev: float = 2.0) -> pd.DataFrame:
    """Add basic Bollinger Band columns to ``df`` and return it."""
    df["bb_mid"] = df["close"].rolling(period).mean()
    df["bb_std"] = df["close"].rolling(period).std()
    df["bb_upper"] = df["bb_mid"] + stddev * df["bb_std"]
    df["bb_lower"] = df["bb_mid"] - stddev * df["bb_std"]
    return df


def is_bollinger_breakout(df: pd.DataFrame, direction: str) -> bool:
    if direction == "buy":
        return df["close"].iloc[-1] > df["bb_upper"].iloc[-1]
    if direction == "sell":
        return df["close"].iloc[-1] < df["bb_lower"].iloc[-1]
    return False


def calculate_sl_tp(entry_price: float, regime: str, atr: float, direction: str, rr_ratio: float = 2.0) -> tuple[float, float]:
    """Adaptive SL/TP distances based on regime and ATR."""
    atr_multiplier = {
        "ranging": 1.0,
        "volatile": 1.5,
        "uptrend": 1.2,
        "downtrend": 1.2,
        "trending": 1.3,
    }.get(regime, 1.0)

    sl_distance = atr * atr_multiplier
    tp_distance = sl_distance * rr_ratio

    if direction == "buy":
        return entry_price - sl_distance, entry_price + tp_distance
    return entry_price + sl_distance, entry_price - tp_distance


class TrendBreakoutStrategy(BaseStrategy):
    """Breakout strategy that waits for pullbacks within a trend."""

    def __init__(self) -> None:
        self.signal: str | None = None
        self.stop_loss: float | None = None
        self.take_profit: float | None = None

    def analyze(self, df: pd.DataFrame) -> None:
        self.signal = None
        if len(df) < 30:
            return

        regime = detect_market_regime(df)
        df = add_bollinger_bands(df.copy())
        if "atr" not in df.columns:
            df["atr"] = calculate_atr(df)
        atr = df["atr"].iloc[-1]

        if regime in {"uptrend", "downtrend", "trending"}:
            if is_trend_continuation(df, regime):
                direction = "buy" if regime == "uptrend" else "sell"
                if is_bollinger_breakout(df, direction):
                    entry_price = df["close"].iloc[-1]
                    sl, tp = calculate_sl_tp(entry_price, regime, atr, direction)
                    self.stop_loss = sl
                    self.take_profit = tp
                    self.signal = direction

    def should_buy(self) -> bool:
        return self.signal == "buy"

    def should_sell(self) -> bool:
        return self.signal == "sell"

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
        self.analyze(df.copy(deep=True))
        return self.signal

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        self.analyze(df)
        return self.signal
