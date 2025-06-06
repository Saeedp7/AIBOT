# backtesting/strategy_backtest.py

from __future__ import annotations
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


"""Simple backtester evaluating all available strategies.

This module loads OHLCV data for a single symbol and timeframe,
then iterates candle by candle through the data to evaluate
signals from every strategy in the `strategies` folder. When
run directly it prints a ranked summary of performance metrics
for each strategy.
"""


import importlib
import inspect
import os
from typing import Dict, List, Tuple

import pandas as pd

from data.data_collection import collect_ohlcv_data
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators
from config.settings import SYMBOL, TIMEFRAME


def load_strategies() -> Dict[str, object]:
    """Dynamically import and instantiate all strategy classes."""
    strategy_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "strategies"))
    strategies: Dict[str, object] = {}
    for fname in os.listdir(strategy_dir):
        if not fname.endswith(".py"):
            continue
        if fname in {"strategy_selector.py", "__init__.py"}:
            continue
        module_name = f"strategies.{fname[:-3]}"
        module = importlib.import_module(module_name)
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module_name:
                continue
            if name.lower().endswith("strategy"):
                try:
                    strategies[name] = obj()
                except Exception:
                    pass
    return strategies


def load_data(symbol: str = SYMBOL, timeframe: str = TIMEFRAME, limit: int = 1000) -> pd.DataFrame:
    """Load and preprocess historical data for a single symbol/timeframe."""
    raw = collect_ohlcv_data([symbol], [timeframe], limit=limit)
    cleaned = preprocess_ohlcv_data(raw)
    enriched = add_indicators(cleaned)
    return enriched[symbol][timeframe]


def backtest_strategy(strategy: object, data: pd.DataFrame) -> Dict[str, float]:
    """Run a basic backtest for a single strategy."""
    results = {"trades": 0, "wins": 0, "losses": 0, "pnl": 0.0}
    position = None
    entry = 0.0
    tp = 0.0
    sl = 0.0
    size = 100
    for i in range(200, len(data)):
        current = data.iloc[: i + 1]
        price = data["close"].iloc[i]
        high = data["high"].iloc[i]
        low = data["low"].iloc[i]

        if position:
            if position == "buy":
                if low <= sl:
                    pnl = (sl - entry) * size
                    results["losses"] += 1
                    results["trades"] += 1
                    results["pnl"] += pnl
                    position = None
                elif high >= tp:
                    pnl = (tp - entry) * size
                    results["wins"] += 1
                    results["trades"] += 1
                    results["pnl"] += pnl
                    position = None
            else:  # sell
                if high >= sl:
                    pnl = (entry - sl) * size
                    results["losses"] += 1
                    results["trades"] += 1
                    results["pnl"] += pnl
                    position = None
                elif low <= tp:
                    pnl = (entry - tp) * size
                    results["wins"] += 1
                    results["trades"] += 1
                    results["pnl"] += pnl
                    position = None

        if position is None:
            signal = strategy.check_signal(current)
            if signal == "buy":
                position = "buy"
                entry = price
                tp = entry * 1.015
                sl = entry * 0.99
            elif signal == "sell":
                position = "sell"
                entry = price
                tp = entry * 0.985
                sl = entry * 1.01
    return results


def summarize(results: Dict[str, Dict[str, float]]) -> List[Tuple]:
    """Compute summary statistics for each strategy."""
    summary = []
    for name, res in results.items():
        trades = res["trades"]
        wins = res["wins"]
        losses = res["losses"]
        pnl = res["pnl"]
        win_rate = (wins / trades * 100) if trades else 0.0
        summary.append((name, trades, wins, losses, win_rate, pnl))
    summary.sort(key=lambda x: (x[4], x[5]), reverse=True)
    return summary


def run(symbol: str = SYMBOL, timeframe: str = TIMEFRAME, limit: int = 1000) -> None:
    data = load_data(symbol, timeframe, limit)
    strategies = load_strategies()
    results: Dict[str, Dict[str, float]] = {}
    for name, strat in strategies.items():
        res = backtest_strategy(strat, data)
        results[name] = res
    table = summarize(results)
    print(f"\nResults for {symbol} [{timeframe}]\n")
    header = f"{'Strategy':20} {'Trades':6} {'Wins':5} {'Losses':7} {'WinRate%':8} {'PnL':10}"
    print(header)
    print("-" * len(header))
    for row in table:
        print(f"{row[0]:20} {row[1]:6d} {row[2]:5d} {row[3]:7d} {row[4]:8.2f} {row[5]:10.2f}")


if __name__ == "__main__":
    run()
