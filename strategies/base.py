from __future__ import annotations

import pandas as pd

class BaseStrategy:
    """Common interface for all strategies."""

    strategy_group: str = "day"
    preferred_tf: str = "M15"
    regimes: list[str] | None = None

    def generate_signal(self, df: pd.DataFrame) -> str | None:
        """Return 'buy', 'sell', or None based on DataFrame."""
        raise NotImplementedError

    def check_signal(self, df: pd.DataFrame) -> str | None:
        """Wrapper used by external modules."""
        return self.generate_signal(df.copy(deep=True))