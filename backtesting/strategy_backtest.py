# backtesting/strategy_backtest.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backtest_engine import BacktestEngine
from strategies.trend_following import TrendFollowingStrategy
from backtesting.trade_report import generate_trade_report
from data.chart_data_handler import get_ohlcv
from connectors.mt5_connector import initialize_mt5, shutdown_mt5

def run_backtest():
    try:
        initialize_mt5()
        data = get_ohlcv(num_bars=500)  # Fetch 500 latest candles
        
        strategy = TrendFollowingStrategy(fast_period=10, slow_period=30)
        backtest = BacktestEngine(strategy, initial_balance=10000, lot_size=0.1, fee_per_trade=0)

        final_balance, trades = backtest.run(data)

        print(f"🏁 Final Balance: ${final_balance:.2f}")
        print(f"📈 Total Trades: {len(trades)}")

        for trade in trades:
            print(trade)
                # --- Then show summary report ---
        from backtesting.trade_report import generate_trade_report
        generate_trade_report(trades, starting_balance=10000)
    except Exception as e:
        print(f"❌ Error during backtest: {e}")
    finally:
        shutdown_mt5()

if __name__ == "__main__":
    run_backtest()
