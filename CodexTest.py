from config.settings import SYMBOL, TIMEFRAME
from data.data_collection import collect_ohlcv_data
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators
from strategies.strategy_selector import StrategySelector
from ai_engine.strategy_selector import load_scores, get_best_signal
from risk_management.stop_loss_manager import calculate_sl_tp
from risk_management.lot_sizing_module import calculate_lot_size
from connectors.mt5_connector import get_account_info
from risk_management.daily_guard import DailyGuard

import MetaTrader5 as mt5
import os

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
print(f"\n✅ Final AI Decision (fallback-safe):", final_decision or "buy")

# Step 4: Position sizing test
print("\n💠 Testing position sizing...")
acct = get_account_info()
entry = df["close"].iloc[-1]

try:
    result = calculate_sl_tp(entry, final_decision or "buy", 1.5, 2.0)
    print("🩠 Raw SL/TP result:", result)

    if isinstance(result, tuple):
        if len(result) == 3:
            sl, tp_levels, regime = result
        elif len(result) == 2:
            sl, tp_levels = result
            regime = "unknown"
        else:
            raise ValueError("Unexpected return format from calculate_sl_tp")
    else:
        raise ValueError("SL/TP result must be a tuple")

    if not isinstance(tp_levels, list):
        tp_levels = [tp_levels]

    sl_distance = abs(entry - sl)
    lot = calculate_lot_size(acct.balance, sl_distance, 1.0, SYMBOL)

    print(f"✅ Volume: {lot}")
    print(f"📉 SL: {round(sl, 2)}")
    print(f"🎯 TP Levels: {[round(float(tp), 2) for tp in tp_levels]}")

    tp_count = len(tp_levels)
    if tp_count < 3:
        print(f"❌ WARNING: Only {tp_count} TP level(s) detected — expected at least 3.")
    elif tp_count > 5:
        print(f"❌ WARNING: {tp_count} TP levels detected — expected max 5.")
    else:
        print(f"✅ TP level count OK: {tp_count}")

except Exception as e:
    print("❌ SL/TP calculation error:", str(e))

# Step 5: DailyGuard mock test
print("\n🛡️ Testing DailyGuard mock logic...")
test_path = "logs/test_guard_log.json"

try:
    guard = DailyGuard(data_file=test_path)
    mock_pnl = -55.0
    guard.record_trade(mock_pnl)

    if guard.hit_limits():
        print("❌ DailyGuard blocked further trades as expected (hit loss limit or max trades).")
    else:
        print("✅ DailyGuard allows trading — within safe daily limits.")

finally:
    if os.path.exists(test_path):
        os.remove(test_path)
