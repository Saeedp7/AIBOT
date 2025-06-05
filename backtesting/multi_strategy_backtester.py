import os
import time
from data.chart_data_handler import get_ohlcv
from ai_engine.decision_engine import evaluate_signals
from execution.order_manager import execute_fake_order
from config.settings import SYMBOLS, TIMEFRAMES, BACKTEST_START_DATE,BACKTEST_END_DATE

from strategies.strategy_selector import StrategySelector   # فرض بر تابعی که همه استراتژی‌ها رو لود می‌کنه

def run_backtest():
    final_results = []
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            print(f"\n🕒 Timeframe: {tf}")
            df = get_ohlcv(symbol, tf, start=BACKTEST_START_DATE, end=BACKTEST_END_DATE)
            if df is None or df.empty:
                print(f"⚠️ Failed to load data for {symbol} [{tf}]")
                continue

            print(f"✅ Loaded data for symbol: {symbol} [{tf}]..")

            balance = 10000
            trades = 0
            position = None

            for i in range(100, len(df)):
                current_data = df.iloc[:i].copy()
                current_price = df.iloc[i]["close"]
                selector = StrategySelector()  # instantiate the selector
                strategies = selector.get_all_strategies()
                best_strategy = evaluate_signals(current_data, strategies, symbol, tf)
                if not best_strategy:
                    continue

                if best_strategy and best_strategy.get_signal(current_data) in ["buy", "sell"]:
                    signal = best_strategy.get_signal(current_data)
                    print(f"📈 {symbol} [{tf}] | {best_strategy.__class__.__name__} => Signal: {signal}")
                    result = execute_fake_order(signal, current_price, balance)
                    balance = result["new_balance"]
                    trades += 1

            final_results.append((symbol, tf, trades, balance))

    print("\n📊 Final Summary Across All Symbols & Timeframes:")
    for symbol, tf, trades, balance in final_results:
        print(f" - {symbol}. [{tf}]: {trades} trades | Final Balance: ${balance}")
    
    print("\n📊 Final Summary Across All Symbols & Timeframes:")
    for symbol, tf, trades, balance in final_results:
        print(f" - {symbol}. [{tf}]: {trades} trades | Final Balance: ${balance:.2f}")

if __name__ == "__main__":
    run_backtest()
