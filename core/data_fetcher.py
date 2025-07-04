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

    async def fetch(self) -> pd.DataFrame:
        """Return processed OHLCV data asynchronously."""

        def _load() -> pd.DataFrame:
            df = get_ohlcv(self.symbol, self.timeframe, num_bars=self.limit)
            df = preprocess_ohlcv_data(df)
            return add_indicators(df)

        return await asyncio.to_thread(_load)
