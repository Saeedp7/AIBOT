# CodexTest.py

import MetaTrader5 as mt5
from config.settings import SYMBOL, TIMEFRAME
from data.data_collection import collect_ohlcv_data
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators
from strategies.strategy_selector import StrategySelector
from ai_engine.strategy_selector import load_scores, get_best_signal
from risk_management.stop_loss_manager import determine_sl_tp  # ✅ Corrected import
from risk_management.lot_sizing_module import calculate_lot_size
from connectors.mt5_connector import get_account_info

# Step 1: Fetch and prepare data
print("📥 Collecting data...")
raw = collect_ohlcv_data([SYMBOL], [TIMEFRAME], limit=300)
clean = preprocess_ohlcv_data(raw)
enriched = add_indicators(clean)
df = enriched[SYMBOL][TIMEFRAME]

# Step 2: Run strategy selector
print("🔍 Running strategy signal check...")
selector = StrategySelector()
signals = selector.check_all(df)
print("\n📊 Signals:")
for name, signal in signals.items():
    print(f"{name:35}: {signal}")

# Step 3: AI selects best decision
scores = load_scores()
final_decision = get_best_signal(signals, scores)
print(f"\n✅ Final AI Decision (fallback-safe): {final_decision or 'buy'}")

# Step 4: Position sizing test
print("\n📐 Testing position sizing...")

acct = get_account_info()
entry = df["close"].iloc[-1]
strategy_name = next((name for name, sig in signals.items() if sig == final_decision), "VWAPReversionStrategy")

# ✅ Use correct SL/TP function with multi-TPs and regime detection
try:
    result = determine_sl_tp(strategy_name, entry, final_decision or "buy", df)
    if not isinstance(result, tuple) or len(result) != 3:
        raise ValueError(f"Unexpected return format from determine_sl_tp: {type(result)}, length = {len(result)}")
except Exception as e:
    print(f"❌ SL/TP calculation error: {e}")
    result = None

if result:
    sl, tp_levels, regime = result
    print(f"🛠️ Raw SL/TP result: {result}")

    # Fallback: convert to list
    if not isinstance(tp_levels, list):
        tp_levels = [tp_levels]

    sl_distance = abs(entry - sl)
    lot = calculate_lot_size(acct.balance, sl_distance, 1.0, SYMBOL)

    print(f"✅ Volume: {lot}")
    print(f"📉 SL: {round(sl, 2)}")
    print(f"🎯 TP Levels: {[round(float(tp), 2) for tp in tp_levels]}")

    # TP count validation
    tp_count = len(tp_levels)
    if tp_count < 3:
        print(f"❌ WARNING: Only {tp_count} TP level(s) detected — expected at least 3.")
    elif tp_count > 5:
        print(f"❌ WARNING: {tp_count} TP levels detected — expected max 5.")
    else:
        print(f"✅ TP level count OK: {tp_count}")
