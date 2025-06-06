# ✅ FIXED: Enhanced Bot Runner

from connectors.mt5_connector import initialize_mt5, shutdown_mt5
from data.chart_data_handler import get_ohlcv, get_latest_price
from strategies import StrategyRegistry
from execution.order_manager import execute_fake_order
from config.settings import SYMBOL, LOT_SIZE, TIMEFRAME

import time

def run_bot():
    try:
        print("🟢 Initializing MT5...")
        initialize_mt5()

        strategy = StrategyRegistry.get_best_strategy(SYMBOL, TIMEFRAME)
        print(f"📊 Strategy Selected: {strategy.name()}")

        while True:
            print("🔄 Checking market...")

            data = get_ohlcv(symbol=SYMBOL, timeframe=TIMEFRAME, num_bars=100)
            price = get_latest_price(SYMBOL)

            if not data or not price:
                print("⚠️ Skipping due to missing data or price...")
                time.sleep(60)
                continue

            signal = strategy.generate_signal(data)

            if signal == "buy":
                execute_fake_order("buy", SYMBOL, LOT_SIZE, price['ask'])
            elif signal == "sell":
                execute_fake_order("sell", SYMBOL, LOT_SIZE, price['bid'])
            else:
                print("❓ No clear signal this cycle.")

            time.sleep(60)  # Wait 1 minute before next check

    except Exception as e:
        print(f"❌ Runtime Error: {e}")

    finally:
        shutdown_mt5()
        print("🛑 MT5 shut down.")

if __name__ == "__main__":
    run_bot()
