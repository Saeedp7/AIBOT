"""End-to-end live decision pipeline for automated trading with debug output."""

from __future__ import annotations
import os
import sys
import json
import MetaTrader5 as mt5

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.data_collection import collect_ohlcv_data
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators
from strategies.strategy_selector import StrategySelector
from ai_engine.strategy_selector import load_scores, get_best_signal
from risk_management.stop_loss_manager import calculate_sl_tp
from config.settings import (
    SYMBOL,
    TIMEFRAME,
    LOT_SIZE,
    STOP_LOSS_MULTIPLIER,
    TAKE_PROFIT_MULTIPLIER,
    MAGIC_NUMBER,
)


def execute_trade(direction: str, symbol: str, lot: float, sl: float, tp: float) -> bool:
    print(f"📤 Executing {direction.upper()} trade on {symbol}...")
    if not mt5.initialize():
        print("❌ Failed to initialize MT5")
        return False

    price = mt5.symbol_info_tick(symbol)
    if price is None:
        print(f"⚠️ No price data for {symbol}")
        mt5.shutdown()
        return False

    deal_type = mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL
    entry_price = price.ask if direction == "buy" else price.bid

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": deal_type,
        "price": entry_price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": MAGIC_NUMBER,
        "comment": "AI Trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    result = mt5.order_send(request)
    mt5.shutdown()

    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"✅ Trade executed: ticket {result.order}")
        return True
    print(f"❌ Trade failed: {result}")
    return False


def make_decision_and_trade(
    symbol: str = SYMBOL,
    timeframe: str = TIMEFRAME,
    lot: float = LOT_SIZE,
    sl_percent: float = STOP_LOSS_MULTIPLIER,
    tp_percent: float = TAKE_PROFIT_MULTIPLIER,
) -> None:
    print("📡 Starting AI Decision Pipeline...")

    print("📥 Collecting market data...")
    raw = collect_ohlcv_data([symbol], [timeframe], limit=300)
    if not raw or symbol not in raw:
        print("❌ Failed to load raw market data.")
        return

    print("🧼 Preprocessing data...")
    clean = preprocess_ohlcv_data(raw)

    print("➕ Adding indicators...")
    enriched = add_indicators(clean)

    df = enriched.get(symbol, {}).get(timeframe)
    if df is None or df.empty:
        print("❌ No enriched data found after indicators.")
        return

    print("🔍 Evaluating strategies...")
    selector = StrategySelector()
    signals: dict[str, str | None] = {}
    for strat in selector.strategies:
        name = strat.__class__.__name__
        try:
            signals[name] = strat.check_signal(df)
        except Exception as exc:
            print(f"⚠️ {name} failed: {exc}")
            signals[name] = None

    print(json.dumps(signals, indent=2))

    print("📊 Loading score memory...")
    scores = load_scores()

    print("🧠 Calculating best signal...")
    decision = get_best_signal(signals, scores)
    print(f"🧠 AI Decision: {decision}")

    if decision in ("buy", "sell"):
        entry = df["close"].iloc[-1]
        sl, tp = calculate_sl_tp(entry, decision, sl_percent, tp_percent)
        success = execute_trade(decision, symbol, lot, sl, tp)
        if success:
            print("🚀 Trade executed successfully.")
        else:
            print("⚠️ Trade execution failed.")
    else:
        print("ℹ️ No trade executed due to low confidence.")

if __name__ == "__main__":
    make_decision_and_trade()
