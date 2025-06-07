"""Utility to fetch historical OHLCV data for multiple symbols and timeframes."""

from typing import Dict
import argparse
import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from connectors.mt5_connector import initialize_mt5, shutdown_mt5, is_connected
from data.chart_data_handler import load_multi_ohlcv
from config.manager import get_config

SYMBOLS = get_config("SYMBOLS", "XAUUSD.,BTCUSD.,ETHUSD.,NDXUSD.,DJIUSD.").split(",")
TIMEFRAMES = get_config("TIMEFRAMES", "M1,M5,M15,H1,H4").split(",")


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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect historical OHLCV data")
    parser.add_argument("--symbols", nargs="*", default=SYMBOLS, help="Symbols list")
    parser.add_argument(
        "--timeframes", nargs="*", default=TIMEFRAMES, help="Timeframes list"
    )
    parser.add_argument("--source", default="MT5", help="MT5 or BINANCE")
    parser.add_argument("--start", help="Start date YYYY-MM-DD HH:MM")
    parser.add_argument("--end", help="End date YYYY-MM-DD HH:MM")
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Number of bars if no date range is supplied",
    )
    parser.add_argument("--to-csv", action="store_true", help="Save data as CSV files")
    parser.add_argument("--csv-dir", default="data/historical", help="CSV output directory")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    datasets = collect_ohlcv_data(
        symbols=args.symbols,
        timeframes=args.timeframes,
        source=args.source,
        start=args.start,
        end=args.end,
        limit=args.limit,
        to_csv=args.to_csv,
        csv_dir=args.csv_dir,
    )
    for sym, tfs in datasets.items():
        for tf, df in tfs.items():
            print(f"{sym} [{tf}] -> {len(df)} rows")