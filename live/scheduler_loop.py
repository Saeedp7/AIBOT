# PATCHED: live/scheduler_loop.py (now uses regime-aware multi-TP SL/TP logic + updates AI memory)

from __future__ import annotations


import time
from datetime import datetime
import argparse
import logging
from typing import Dict, Tuple
import pandas as pd
import MetaTrader5 as mt5

from config.manager import get_config

SYMBOLS = get_config("SYMBOLS", "XAUUSD.,BTCUSD.,ETHUSD.,NDXUSD.,DJIUSD.").split(",")
TIMEFRAMES = get_config("TIMEFRAMES", "M1,M5,M15,H1,H4").split(",")
ACTIVE_SYMBOLS_TIMEFRAMES = {symbol: TIMEFRAMES for symbol in SYMBOLS}
CHECK_INTERVAL_SECONDS = int(get_config("CHECK_INTERVAL_SECONDS", 60))
MAX_RISK_PER_TRADE = float(get_config("MAX_RISK", 0.01))
MAGIC_NUMBER = int(get_config("MAGIC_NUMBER", 123456))
DAILY_LOSS_LIMIT_PERCENT = float(get_config("DAILY_LOSS_LIMIT_PERCENT", 5.0))
MAX_TRADES_PER_DAY = int(get_config("MAX_TRADES_PER_DAY", 20))
LIVE_MODE = get_config("LIVE_MODE", "false")
from data.chart_data_handler import load_multi_ohlcv
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators
from strategies.strategy_selector import StrategySelector
from ai_engine.strategy_selector import load_scores, get_best_signal
from ai_engine.score_updater import update_strategy_score
from risk_management.stop_loss_manager import determine_sl_tp
from risk_management.lot_sizing_module import calculate_lot_size
from risk_management.daily_guard import DailyGuard
from connectors.mt5_connector import get_account_info
from utils.trade_journal import record_trade, update_trade, load_history
from utils.logger import log_trade_action
from risk_management.breakeven_manager import BreakEvenManager
from monitoring.alert_manager import (
    alert_trade_opened,
    alert_sl_moved,
    alert_trade_closed,
    alert_daily_guard,
)
logger = logging.getLogger("scheduler")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live trading scheduler loop")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--silent", action="store_true", help="Suppress info logging")
    return parser.parse_args()

daily_guard = DailyGuard(
    loss_limit_percent=DAILY_LOSS_LIMIT_PERCENT,
    max_trades=MAX_TRADES_PER_DAY,
)

open_trades: list[dict] = []
trade_cache: set[tuple[str, str]] = set()
trade_journal: dict[int, dict] = {}

# Track open trades to avoid duplicates per symbol/timeframe
executed_trades: dict[str, dict[str, int]] = {}

# Cache OHLCV and indicator data per symbol/timeframe
ohlcv_cache: Dict[Tuple[str, str], pd.DataFrame] = {}
indicator_cache: Dict[Tuple[str, str], pd.DataFrame] = {}


def refresh_data(symbol: str, timeframe: str, limit: int = 300) -> None:
    """Fetch and cache OHLCV data with indicators for a symbol/timeframe."""
    raw = load_multi_ohlcv([symbol], [timeframe], num_bars=limit)
    if not raw or symbol not in raw:
        logger.warning("Failed to load data for %s %s", symbol, timeframe)
        return
    clean = preprocess_ohlcv_data(raw)
    ohlcv_cache[(symbol, timeframe)] = clean[symbol][timeframe]
    enriched = add_indicators(clean)
    indicator_cache[(symbol, timeframe)] = enriched[symbol][timeframe]

def execute_trade(direction: str, symbol: str, lot: float, sl: float, tp: float) -> int | None:

    price = mt5.symbol_info_tick(symbol)
    if price is None:
        logging.warning(f"No price data for {symbol}")
        return None

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

    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        logger.info("Trade executed: ticket %s", result.order)
        return result.order
    logger.error("Trade failed: %s", result)
    return None


def run_open_trade_manager() -> None:
    """Update open trades: breakeven and trailing stops."""
    for trade in list(open_trades):
        tick = mt5.symbol_info_tick(trade["symbol"])
        if not tick:
            continue
        price = tick.bid if trade["direction"] == "sell" else tick.ask
        next_idx = trade.get("tp_hit_index", -1) + 1
        if next_idx < len(trade["tp_levels"]):
            target = trade["tp_levels"][next_idx]
            hit = price <= target if trade["direction"] == "sell" else price >= target
            if hit:
                trade["tp_hit_index"] = next_idx
                if next_idx == 0:
                    trade["sl"] = trade["entry"]
                else:
                    trade["sl"] = trade["tp_levels"][next_idx - 1]
                log_trade_action(f"{trade['symbol']} {trade['timeframe']} TP{next_idx+1} hit, SL moved to {trade['sl']}")
                trade_journal[trade["id"]]["modified"] = True
                alert_sl_moved(trade["symbol"], trade["timeframe"], trade["sl"])

        stop_hit = price >= trade["sl"] if trade["direction"] == "sell" else price <= trade["sl"]
        if stop_hit:
            log_trade_action(f"Close {trade['symbol']} {trade['timeframe']} @ {price}")
            trade_journal[trade["id"]]["closed"] = True
            open_trades.remove(trade)
            trade_cache.discard((trade["symbol"], trade["timeframe"]))
            alert_trade_closed(trade["symbol"], trade["timeframe"], "stop_hit")


def process_symbol_timeframe(symbol: str, timeframe: str) -> None:
    if daily_guard.hit_limits():
        logger.warning("Daily risk guard triggered.")
        alert_daily_guard("limits hit")
        return

    if (symbol, timeframe) in trade_cache:
        logger.debug("Trade already open for %s %s", symbol, timeframe)
        return
    if executed_trades.get(symbol, {}).get(timeframe):
        logger.debug("Existing trade for %s %s, skipping execution", symbol, timeframe)
        return
    df = indicator_cache.get((symbol, timeframe))
    if df is None or df.empty:
        logger.warning("No cached data for %s %s", symbol, timeframe)
        return

    selector = StrategySelector()
    signals: dict[str, str | None] = {}
    for strat in selector.strategies:
        name = strat.__class__.__name__
        try:
            signals[name] = strat.check_signal(df)
        except Exception as exc:
            logger.warning("%s failed: %s", name, exc)
            signals[name] = None

    scores = load_scores()
    decision = get_best_signal(signals, scores)
    if decision not in ("buy", "sell"):
        logger.info("No action for %s %s", symbol, timeframe)
        return


    entry = df["close"].iloc[-1]
    best_strat = max((k for k, v in signals.items() if v == decision),
                     key=lambda s: scores.get(s, {}).get("recent_score", 0.0),
                     default=None)
    if not best_strat:
        logger.error("No confident strategy to assign score update")
        return

    sl, tp_levels, regime = determine_sl_tp(best_strat, entry, decision, df)
    acct = mt5.account_info()
    lot = calculate_lot_size(acct.balance, abs(entry - sl), MAX_RISK_PER_TRADE * 100, symbol)

    logger.info(
        "%s %s → %s @ %s | SL: %s TP1: %s Lot: %s",
        symbol,
        timeframe,
        decision.upper(),
        entry,
        sl,
        tp_levels[0],
        lot,
    )
    ticket = execute_trade(decision, symbol, lot, sl, tp_levels[0])
    if ticket:
        daily_guard.record_trade(0)
        executed_trades.setdefault(symbol, {})[timeframe] = ticket
        record_trade(
            symbol=symbol,
            timeframe=timeframe,
            entry=entry,
            sl=sl,
            tps=tp_levels,
            strategy=best_strat,
            result="open",
            ticket=ticket,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )
        alert_trade_opened(symbol, timeframe, decision, entry, sl, tp_levels[0])


def run_live_trade_manager() -> None:
    """Monitor open positions and adjust stops or close early."""
    positions = mt5.positions_get()
    history = {t["ticket"]: t for t in load_history()}
    if positions is None:
        return
    for pos in positions:
        ticket = pos.ticket
        rec = history.get(ticket)
        if not rec:
            continue
        direction = "buy" if pos.type == mt5.POSITION_TYPE_BUY else "sell"
        tick = mt5.symbol_info_tick(pos.symbol)
        if not tick:
            continue
        price = tick.bid if direction == "sell" else tick.ask
        bem = BreakEvenManager(rec["entry"], direction, pos.sl, rec.get("tp", []))
        new_sl = bem.update_stop_loss(price)
        if new_sl != pos.sl:
            req = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": new_sl,
                "tp": pos.tp,
            }
            res = mt5.order_send(req)
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                log_trade_action(
                    f"SL moved to breakeven for {pos.symbol} on {rec['timeframe']} by TradeManager"
                )
                update_trade(ticket, sl=new_sl, sl_moved=True)
                alert_sl_moved(pos.symbol, rec["timeframe"], new_sl)
                if new_sl == rec["entry"] and rec.get("result") == "open":
                    update_trade(ticket, result="TP1 hit")
                    update_strategy_score(rec["strategy"], "win", regime=rec.get("regime", ""))
        # simple reversal check
        if direction == "buy" and price < rec["entry"] - (rec["entry"] - rec["sl"]):
            close_type = mt5.ORDER_TYPE_SELL
        elif direction == "sell" and price > rec["entry"] + (rec["sl"] - rec["entry"]):
            close_type = mt5.ORDER_TYPE_BUY
        else:
            close_type = None
        if close_type is not None:
            close_req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": MAGIC_NUMBER,
                "comment": "TradeManager close",
            }
            res = mt5.order_send(close_req)
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                log_trade_action(
                    f"Trade closed early on trend reversal: {pos.symbol} {rec['timeframe']}"
                )
                update_trade(ticket, result="closed_early", closed_early=True)
                update_strategy_score(rec["strategy"], "loss", regime=rec.get("regime", ""))
                executed_trades.get(pos.symbol, {}).pop(rec["timeframe"], None)
                alert_trade_closed(pos.symbol, rec["timeframe"], "closed_early")


def scheduler_loop(args: argparse.Namespace) -> None:
    level = logging.DEBUG if args.debug else (logging.ERROR if args.silent else logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")
    while True:
        if not mt5.initialize():
            logger.error("Failed to initialize MT5")
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue
        try:
            run_open_trade_manager()
            run_live_trade_manager()
            for symbol, tfs in ACTIVE_SYMBOLS_TIMEFRAMES.items():
                for tf in tfs:
                    refresh_data(symbol, tf)
                    process_symbol_timeframe(symbol, tf)
        finally:
            mt5.shutdown()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    scheduler_loop(_parse_args())
