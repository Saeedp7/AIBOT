"""Convenience module for fetching historical OHLCV data."""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import Dict
import argparse

import pandas as pd
from connectors.mt5_connector import initialize_mt5, shutdown_mt5
from data.chart_data_handler import load_multi_ohlcv
from config.settings import SYMBOLS, TIMEFRAMES

def collect(
    symbols=SYMBOLS,
    timeframes=TIMEFRAMES,
    source: str = "MT5",
    start: str | None = None,
    end: str | None = None,
    limit: int = 500,
    to_csv: bool = False,
    csv_dir: str = "data/historical",
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """Collect OHLCV datasets for multiple symbols and timeframes."""
    need_mt5 = source.upper() != "BINANCE"
    if need_mt5:
        initialize_mt5()
    try:
        return load_multi_ohlcv(
            symbols,
            timeframes,
            source=source,
            start=start,
            end=end,
            num_bars=limit,
            to_csv=to_csv,
            csv_dir=csv_dir,
        )
    finally:
        if need_mt5:
            shutdown_mt5()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect historical OHLCV data")
    parser.add_argument("--symbols", nargs="*", default=SYMBOLS, help="Symbols list")
    parser.add_argument("--timeframes", nargs="*", default=TIMEFRAMES, help="Timeframes list")
    parser.add_argument("--source", default="MT5", help="MT5 or BINANCE")
    parser.add_argument("--start", help="Start date YYYY-MM-DD HH:MM")
    parser.add_argument("--end", help="End date YYYY-MM-DD HH:MM")
    parser.add_argument("--limit", type=int, default=500, help="Number of bars if no date range")
    parser.add_argument("--to-csv", action="store_true", help="Save data as CSV files")
    parser.add_argument("--csv-dir", default="data/historical", help="CSV output directory")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    datasets = collect(
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