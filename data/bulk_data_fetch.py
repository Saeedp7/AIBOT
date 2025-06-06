"""Utility for downloading historical OHLCV data."""

from typing import Dict, List

import argparse

from connectors.mt5_connector import initialize_mt5, shutdown_mt5
from config.settings import SYMBOLS, TIMEFRAMES
from data.chart_data_handler import load_multi_ohlcv


def fetch_all(
    symbols=SYMBOLS,
    timeframes=TIMEFRAMES,
    source: str = "MT5",
    start: str | None = None,
    end: str | None = None,
    num_bars: int = 100,
    to_csv: bool = False,
    csv_dir: str = "data/historical",
) -> Dict[str, Dict[str, "pd.DataFrame"]]:
    """Fetch OHLCV data for multiple symbols/timeframes.

    Parameters
    ----------
    symbols : list[str]
        List of instrument symbols to download.
    timeframes : list[str]
        Timeframes such as ``["M5", "H1"]``.
    source : str
        ``"MT5"`` or ``"BINANCE"``.
    start, end : str | None
        Optional start/end timestamps ("YYYY-MM-DD HH:MM").
    num_bars : int
        Number of bars if ``start``/``end`` are not provided.
    to_csv : bool
        Save each dataset as ``<symbol>_<tf>.csv`` when ``True``.
    csv_dir : str
        Destination directory for CSV files.

    Returns
    -------
    Dict[str, Dict[str, pd.DataFrame]]
        Nested dictionary ``{symbol: {timeframe: DataFrame}}``.
    """

    need_mt5 = source.upper() != "BINANCE"
    if need_mt5:
        initialize_mt5()

    try:
        datasets = load_multi_ohlcv(
            symbols,
            timeframes,
            source=source,
            start=start,
            end=end,
            num_bars=num_bars,
            to_csv=to_csv,
            csv_dir=csv_dir,
        )

        for symbol, tfs in datasets.items():
            for tf, df in tfs.items():
                print(f"{symbol} [{tf}] -> {len(df)} rows")

        return datasets
    finally:
        if need_mt5:
            shutdown_mt5()
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download historical OHLCV data")
    parser.add_argument("--symbols", nargs="*", default=SYMBOLS, help="Symbols list")
    parser.add_argument("--timeframes", nargs="*", default=TIMEFRAMES, help="Timeframes list")
    parser.add_argument("--source", default="MT5", help="MT5 or BINANCE")
    parser.add_argument("--start", help="Start date YYYY-MM-DD HH:MM")
    parser.add_argument("--end", help="End date YYYY-MM-DD HH:MM")
    parser.add_argument("--num-bars", type=int, default=100, help="Number of bars")
    parser.add_argument("--to-csv", action="store_true", help="Save to CSV files")
    parser.add_argument("--csv-dir", default="data/historical", help="CSV output directory")
    return parser.parse_args()

if __name__ == "__main__":
    args = _parse_args()
    fetch_all(
        symbols=args.symbols,
        timeframes=args.timeframes,
        source=args.source,
        start=args.start,
        end=args.end,
        num_bars=args.num_bars,
        to_csv=args.to_csv,
        csv_dir=args.csv_dir,
    )