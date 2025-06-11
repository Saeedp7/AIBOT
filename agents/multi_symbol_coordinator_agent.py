from __future__ import annotations

from typing import Iterable, Tuple


class MultiSymbolCoordinatorAgent:
    """Cycle through symbol/timeframe combinations."""

    def __init__(self, symbols: Iterable[str], timeframes: Iterable[str]):
        self.symbols = list(symbols)
        self.timeframes = list(timeframes)
        self._index = -1

    def next_pair(self) -> Tuple[str, str]:
        total = len(self.symbols) * len(self.timeframes)
        if total == 0:
            raise ValueError("No symbols/timeframes configured")
        self._index = (self._index + 1) % total
        s_idx = self._index // len(self.timeframes)
        t_idx = self._index % len(self.timeframes)
        return self.symbols[s_idx], self.timeframes[t_idx]