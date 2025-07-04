"""Async data fetching utilities."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import pandas as pd

from data.chart_data_handler import get_ohlcv
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators


@dataclass
class DataFetcher:
    """Fetch OHLCV and indicator data for a symbol/timeframe."""

    symbol: str
    timeframe: str
    limit: int = 300

    async def fetch(self) -> pd.DataFrame | None:
        """Return processed OHLCV data asynchronously.

        If fetching fails, ``None`` is returned so callers can
        gracefully skip the symbol/timeframe without crashing the
        scheduler loop.
        """

        def _load() -> pd.DataFrame | None:
            if not self.symbol or not self.timeframe:
                import logging

                logging.getLogger(__name__).error(
                    "Data fetch failed: blank symbol or timeframe"
                )
                return None
            try:
                raw = {
                    self.symbol: {
                        self.timeframe: get_ohlcv(
                            self.symbol, self.timeframe, num_bars=self.limit
                        )
                    }
                }
                cleaned = preprocess_ohlcv_data(raw)
                enriched = add_indicators(cleaned)
                return enriched[self.symbol][self.timeframe]
            except Exception as exc:  # pragma: no cover - network/mt5 failure
                import logging

                logging.getLogger(__name__).error(
                    "Data fetch failed for %s %s: %s",
                    self.symbol,
                    self.timeframe,
                    exc,
                )
                return None

        return await asyncio.to_thread(_load)
