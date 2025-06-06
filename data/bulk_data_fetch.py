from connectors.mt5_connector import initialize_mt5, shutdown_mt5
from config.settings import SYMBOLS, TIMEFRAMES
from data.chart_data_handler import load_multi_ohlcv


def fetch_all():
    try:
        initialize_mt5()
        datasets = load_multi_ohlcv(SYMBOLS, TIMEFRAMES, num_bars=100)
        for symbol, tfs in datasets.items():
            for tf, df in tfs.items():
                print(f"{symbol} [{tf}] -> {len(df)} rows")
    finally:
        shutdown_mt5()


if __name__ == "__main__":
    fetch_all()