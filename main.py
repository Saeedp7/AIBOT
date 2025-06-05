# main.py

from connectors.mt5_connector import initialize_mt5, shutdown_mt5
from data.chart_data_handler import get_ohlcv, get_latest_price
from strategies.trend_following import TrendFollowingStrategy
from execution.order_manager import execute_fake_order
from config.settings import SYMBOL, LOT_SIZE

import time

def run_bot():
    try:
        initialize_mt5()
        strategy = TrendFollowingStrategy(fast_period=10, slow_period=30)

        while True:
            print("🔄 Checking market...")
            data = get_ohlcv(num_bars=100)
            price = get_latest_price()

            strategy.analyze(data)

            if strategy.should_buy():
                execute_fake_order("buy", SYMBOL, LOT_SIZE, price['ask'])
            elif strategy.should_sell():
                execute_fake_order("sell", SYMBOL, LOT_SIZE, price['bid'])
            else:
                print("❓ No clear signal this cycle.")

            time.sleep(60)  # Wait 1 minute before next check

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        shutdown_mt5()

if __name__ == "__main__":
    run_bot()
