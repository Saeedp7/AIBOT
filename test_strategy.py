# test_strategy.py

from connectors.mt5_connector import initialize_mt5, shutdown_mt5
from data.chart_data_handler import get_ohlcv
from strategies.trend_following import TrendFollowingStrategy

def test_strategy():
    try:
        initialize_mt5()
        data = get_ohlcv(num_bars=100)
        strategy = TrendFollowingStrategy(fast_period=10, slow_period=30)
        strategy.analyze(data)

        if strategy.should_buy():
            print("📈 BUY Signal detected!")
        elif strategy.should_sell():
            print("📉 SELL Signal detected!")
        else:
            print("❓ No clear signal.")
    except Exception as e:
        print(e)
    finally:
        shutdown_mt5()

if __name__ == "__main__":
    test_strategy()
