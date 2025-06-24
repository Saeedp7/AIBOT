from __future__ import annotations

from typing import Tuple

import pandas as pd

from data.chart_data_handler import load_multi_ohlcv
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators
from ai_engine.regime_classifier import detect_market_regime


class MarketScannerAgent:
    """Fetch and preprocess OHLCV data, returning regime classification."""

    def __init__(self, bars: int = 300) -> None:
        self.bars = bars

    def scan(self, symbol: str, timeframe: str) -> Tuple[pd.DataFrame | None, str]:
        raw = load_multi_ohlcv([symbol], [timeframe], num_bars=self.bars)
        if not raw or symbol not in raw:
            return None, "unknown"
        data = preprocess_ohlcv_data(raw)
        df = data[symbol][timeframe]
        enriched = add_indicators(data)
        df = enriched[symbol][timeframe]
        regime = detect_market_regime(df, symbol=symbol)
        return df, regime