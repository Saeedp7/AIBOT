from __future__ import annotations
import warnings
warnings.simplefilter(action='ignore', category=UserWarning)

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from data.data_collection import collect_ohlcv_data
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators
from strategies.strategy_selector import StrategySelector
from ai_engine.strategy_selector import get_best_signal, load_scores
from config.settings import SYMBOL, TIMEFRAME

# === Step 1: Load historical data ===
print("📥 Collecting data for:", SYMBOL, TIMEFRAME)
raw_data = collect_ohlcv_data([SYMBOL], [TIMEFRAME], limit=300)
cleaned_data = preprocess_ohlcv_data(raw_data)
enriched_data = add_indicators(cleaned_data)
df = enriched_data[SYMBOL][TIMEFRAME]

# === Step 2: Evaluate all strategies ===
print("🔍 Running strategy signal check...")
selector = StrategySelector()
signals = {}
for strategy in selector.strategies:
    name = strategy.__class__.__name__
    try:
        signal = strategy.check_signal(df)
        signals[name] = signal
    except Exception as e:
        print(f"⚠️ {name} failed: {e}")
        signals[name] = None

print("\n📊 Signals:")
for strat, sig in signals.items():
    print(f"{strat:35}: {sig}")

# === Step 3: Load score memory ===
scores = load_scores()

# === Step 4: AI Decision ===
final_signal = get_best_signal(signals, scores)

print("\n✅ Final AI Decision:", final_signal)
