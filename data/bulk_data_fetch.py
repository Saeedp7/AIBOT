"""Utility for downloading historical OHLCV data."""

from typing import Dict

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
        datasets = load_multi_ohlcv(SYMBOLS, TIMEFRAMES, num_bars=100)

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
        shutdown_mt5()
        if need_mt5:
            shutdown_mt5()


if __name__ == "__main__":
    fetch_all()