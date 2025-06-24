from __future__ import annotations

import pandas as pd

class BaseStrategy:
    """Common interface for all strategies."""

    strategy_group: str = "day"
    preferred_tf: str = "M15"
    regimes: list[str] | None = None
    # Allowed market regimes for this strategy. Scheduler will block trades if
    # the detected regime is not listed here.  Defaults to trending only.
    ALLOWED_REGIMES: set[str] = {"trending"}
    def generate_signal(self, df: pd.DataFrame) -> str | None:
        """Return 'buy', 'sell', or None based on DataFrame."""
        raise NotImplementedError

    def check_signal(
            self,
            df: pd.DataFrame,
            *,
            symbol: str | None = None,
            timeframe: str | None = None,
            regime: str | None = None,
        ) -> str | None:
            """Wrapper used by external modules.

            Adds debug logging so we can confirm strategy evaluation is occurring for
            each symbol/timeframe.
            """
            import logging

            logger = logging.getLogger(__name__)
            if isinstance(df, pd.DataFrame):
                price = df["close"].iloc[-1] if "close" in df.columns else float("nan")
                data = df.copy(deep=True)
            else:
                price = float("nan")
                data = df
            logger.debug(
                f"[{self.__class__.__name__}] Called on {symbol or ''} {timeframe or ''}"
                f" Regime: {regime or 'unknown'}, Price: {price}"
            )
            return self.generate_signal(data)