# PATCHED: live/scheduler_loop.py (now uses regime-aware multi-TP SL/TP logic + updates AI memory)

from __future__ import annotations

import os
import sys
import time
import MetaTrader5 as mt5

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import (
    ACTIVE_SYMBOLS_TIMEFRAMES,
    CHECK_INTERVAL_SECONDS,
    MAX_RISK_PER_TRADE,
    MAGIC_NUMBER,
    DAILY_LOSS_LIMIT_PERCENT,
    MAX_TRADES_PER_DAY,
)
from data.data_collection import collect_ohlcv_data
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators
from strategies.strategy_selector import StrategySelector
from ai_engine.strategy_selector import load_scores, get_best_signal
from ai_engine.score_updater import update_scores
from risk_management.stop_loss_manager import determine_sl_tp
from risk_management.lot_sizing_module import calculate_lot_size
from risk_management.daily_guard import DailyGuard
from connectors.mt5_connector import get_account_info

daily_guard = DailyGuard(
    loss_limit_percent=DAILY_LOSS_LIMIT_PERCENT,
    max_trades=MAX_TRADES_PER_DAY,
)

def execute_trade(direction: str, symbol: str, lot: float, sl: float, tp: float) -> bool:
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


def process_symbol_timeframe(symbol: str, timeframe: str) -> None:
    raw = collect_ohlcv_data([symbol], [timeframe], limit=300)
    if not raw or symbol not in raw:
        print(f"❌ Failed to load data for {symbol} {timeframe}")
        return
    clean = preprocess_ohlcv_data(raw)
    enriched = add_indicators(clean)
    df = enriched[symbol][timeframe]
    if df is None or df.empty:
        print(f"⚠️ No data after indicators for {symbol} {timeframe}")
        return

    selector = StrategySelector()
    signals: dict[str, str | None] = {}
    for strat in selector.strategies:
        name = strat.__class__.__name__
        try:
            signals[name] = strat.check_signal(df)
        except Exception as exc:
            print(f"⚠️ {name} failed: {exc}")
            signals[name] = None

    scores = load_scores()
    decision = get_best_signal(signals, scores)
    if decision not in ("buy", "sell"):
        print(f"ℹ️ No action for {symbol} {timeframe}")
        return

    if daily_guard.hit_limits():
        print("🚫 Daily risk guard triggered.")
        return

    entry = df["close"].iloc[-1]
    best_strat = max((k for k, v in signals.items() if v == decision),
                     key=lambda s: scores.get(s, {}).get("recent_score", 0.0),
                     default=None)
    if not best_strat:
        print("❌ No confident strategy to assign score update.")
        return

    sl, tp_levels, regime = determine_sl_tp(best_strat, entry, decision, df)
    acct = get_account_info()
    lot = calculate_lot_size(acct.balance, abs(entry - sl), MAX_RISK_PER_TRADE * 100, symbol)

    print(f"📈 {symbol} {timeframe} → {decision.upper()} @ {entry} | SL: {sl} TP1: {tp_levels[0]} Lot: {lot}")
    if execute_trade(decision, symbol, lot, sl, tp_levels[0]):
        daily_guard.record_trade(0)
        result_metrics = {best_strat: {"win_rate": 50.0, "recent_score": 0.9, "regime_fit": 1.0}}  # TODO: dynamic score
        update_scores(result_metrics)


def scheduler_loop() -> None:
    while True:
        for symbol, tfs in ACTIVE_SYMBOLS_TIMEFRAMES.items():
            for tf in tfs:
                process_symbol_timeframe(symbol, tf)
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    scheduler_loop()
