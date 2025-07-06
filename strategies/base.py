from __future__ import annotations

import pandas as pd
from utils.logger import debug_log
from utils.indicators import (
    calculate_ema, calculate_sma, calculate_rsi, calculate_macd,
    calculate_vwap, calculate_bollinger_bands, calculate_adx, calculate_supertrend
)
from strategy_components.session_filter import killzone_label

class BaseStrategy:

    """Common interface for all strategies."""

    strategy_group: str = "day"
    preferred_tf: str = "M15"
    regimes: list[str] | None = None
    # Allowed market regimes for this strategy. Scheduler will block trades if
    # the detected regime is not listed here.  Defaults to trending only.
    ALLOWED_REGIMES: set[str] = {"trending", "volatile"}

    def is_volatile_enough(self, atr_series: pd.Series, threshold: float = 0.001) -> bool:
        """Return True if the latest ATR value exceeds the threshold."""
        return atr_series.iloc[-1] > threshold
    
    def allowed_regimes(self) -> list[str]:
        """Return allowed market regimes for this strategy."""
        from config.settings import DEFAULT_ALLOWED_REGIMES

        if self.regimes:
            return list(self.regimes)
        return list(getattr(self, "ALLOWED_REGIMES", set(DEFAULT_ALLOWED_REGIMES)))

    def _log_context(
        self,
        df: pd.DataFrame,
        *,
        pattern_detected: str | None = None,
        entry_zone: str | None = None,
        bias: str | None = None,
    ) -> None:
        """Log indicator values and contextual tags for debugging."""
        if df is None or df.empty:
            return
        values: list[str] = []
        if "rsi_14" in df.columns:
            values.append(f"RSI={df['rsi_14'].iloc[-1]:.2f}")
        if "ema_20" in df.columns:
            values.append(f"EMA20={df['ema_20'].iloc[-1]:.2f}")
        if "ema_50" in df.columns:
            values.append(f"EMA50={df['ema_50'].iloc[-1]:.2f}")
        if "atr" in df.columns:
            values.append(f"ATR={df['atr'].iloc[-1]:.2f}")
        if "vwap" in df.columns:
            values.append(f"VWAP={df['vwap'].iloc[-1]:.2f}")
        if "ITS_9" in df.columns:
            values.append(f"Tenkan={df['ITS_9'].iloc[-1]:.2f}")
        session = killzone_label(df.index[-1].to_pydatetime())
        msg = (
            f"{self.__class__.__name__} "
            + " ".join(values)
            + f" pattern={pattern_detected} entry_zone={entry_zone} bias={bias} session={session}"
        )
        debug_log(msg)

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        """Return 'buy', 'sell', or None based on DataFrame."""
        raise NotImplementedError

    def check_signal(
                   self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        regime: str,
    ) -> str | None:
        """Fallback wrapper used by external modules."""
        df = df.copy(deep=True)
        df['ema_20'] = calculate_ema(df['close'], 20)
        df['vwap'] = calculate_vwap(df)
        return self.generate_signal(df)