"""Utility to fetch historical OHLCV data for multiple symbols and timeframes."""

from typing import Dict
import pandas as pd

from connectors.mt5_connector import initialize_mt5, shutdown_mt5, is_connected
from data.chart_data_handler import load_multi_ohlcv
from config.settings import SYMBOLS, TIMEFRAMES


def collect_ohlcv_data(
    symbols=SYMBOLS,
    timeframes=TIMEFRAMES,
    source: str = "MT5",
    start: str | None = None,
    end: str | None = None,
    limit: int = 500,
    to_csv: bool = False,
    csv_dir: str = "data/historical",
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """Collect OHLCV datasets for each symbol/timeframe.

    Parameters
    ----------
    symbols : list[str]
        Trading symbols to fetch.
    timeframes : list[str]
        Timeframes like "M5" or "H1".
    source : str
        "MT5" or "BINANCE". Defaults to MT5.
    start, end : str | None
        Optional date range in ``YYYY-MM-DD HH:MM``.
    limit : int
        Number of bars if no date range is supplied.
    to_csv : bool
        If ``True``, save each dataset to ``csv_dir``.
    csv_dir : str
        Output directory when ``to_csv`` is enabled.
    """
    use_mt5 = source.upper() == "MT5"
    if use_mt5:
        if not initialize_mt5():
            raise RuntimeError(
                "Failed to connect to MetaTrader5. Check installation and credentials."
            )

    try:
        data = load_multi_ohlcv(
            symbols,
            timeframes,
            source=source,
            start=start,
            end=end,
            num_bars=limit,
            to_csv=to_csv,
            csv_dir=csv_dir,
        )
        return data
    finally:
        if use_mt5 and is_connected():
            shutdown_mt5()