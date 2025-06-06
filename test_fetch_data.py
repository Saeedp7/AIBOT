# test_fetch_data.py

from connectors.mt5_connector import initialize_mt5, shutdown_mt5
from data.chart_data_handler import get_ohlcv, get_latest_price

def test_data_fetch() -> None:
    try:
        initialize_mt5()
        candles = get_ohlcv(num_bars=100)
        print(candles)

        price = get_latest_price()
        print(f"Current Price: {price}")
    except Exception as e:
        print(e)
    finally:
        shutdown_mt5()

if __name__ == "__main__":
    test_data_fetch()
