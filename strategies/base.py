from __future__ import annotations

import pandas as pd

class BaseStrategy:
    """Common interface for all strategies."""

    strategy_group: str = "day"
    preferred_tf: str = "M15"
    regimes: list[str] | None = None
    # Allowed market regimes for this strategy. Scheduler will block trades if
    # the detected regime is not listed here.  Defaults to trending only.
    ALLOWED_REGIMES: set[str] = {"trending", "volatile"}
    
    def allowed_regimes(self) -> list[str]:
        """Return allowed market regimes for this strategy."""
        from config.settings import DEFAULT_ALLOWED_REGIMES

        if self.regimes:
            return list(self.regimes)
        return list(getattr(self, "ALLOWED_REGIMES", set(DEFAULT_ALLOWED_REGIMES)))
    
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
        return self.generate_signal(df)