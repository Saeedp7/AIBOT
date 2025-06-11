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
CONFIDENCE_THRESHOLD = float(get_config("CONFIDENCE_THRESHOLD", 0.5))
from data.chart_data_handler import load_multi_ohlcv
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators
from strategies.strategy_selector import StrategySelector
from agents.strategy_selector_agent import StrategySelectorAgent
from ai_engine.strategy_selector import load_scores
from ai_engine.score_updater import update_strategy_score
from risk_management.core import prepare_trade_parameters
from risk_management.daily_guard import DailyGuard
from risk_management.exposure_guard import ExposureGuard
from connectors.mt5_connector import get_account_info
from utils.trade_journal import record_trade, update_trade, load_history
from utils.logger import log_trade_action
from risk_management.breakeven_manager import BreakEvenManager
from execution.order_manager import execute_fake_order
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


trade_cache: set[tuple[str, str]] = set()
strategy_selector_agent = StrategySelectorAgent(StrategySelector().strategies)

# Track open trades to avoid duplicates per symbol/timeframe
executed_trades: dict[str, dict[str, int]] = {}

# Exposure guard to manage per-symbol stacking
exposure_guard = ExposureGuard()

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

    entry_price = price.ask if direction == "buy" else price.bid
    if get_config("LIVE_MODE", "false").lower() != "true":
        execute_fake_order(direction, symbol, lot, entry_price, sl=sl, tp=tp)
        return int(time.time())

    deal_type = mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL
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

    decision, best_strat, market_regime = strategy_selector_agent.select(symbol, timeframe)
    if decision not in ("buy", "sell") or not best_strat:
        logger.info("No action for %s %s", symbol, timeframe)
        return


    entry = df["close"].iloc[-1]
    scores = load_scores()
    metrics = scores.get(best_strat, {})
    confidence = (
        float(metrics.get("recent_score", 0.0))
        * float(metrics.get("regime_fit", 0.0))
        * float(metrics.get("win_rate", 0.0))
    )
    log_trade_action(
        f"Confidence {confidence:.4f} for {symbol} {timeframe} using {best_strat}"
    )
    if confidence < CONFIDENCE_THRESHOLD:
        log_trade_action(
            f"Skipping trade for {symbol} {timeframe}: confidence {confidence:.4f} < {CONFIDENCE_THRESHOLD}"
        )
        return
    if not exposure_guard.allow(symbol, timeframe, decision, confidence):
        log_trade_action(
            f"🚫 Exposure guard blocked trade: {symbol} {timeframe} {decision}"
        )
        return

    acct = mt5.account_info()
    prep = prepare_trade_parameters(
        symbol=symbol,
        strategy_name=best_strat,
        direction=decision,
        entry_price=entry,
        market_data=df,
        account_balance=acct.balance,
        risk_percent=MAX_RISK_PER_TRADE * 100,
        guard=daily_guard,
    )
    if not prep:
        logger.info("Risk guard prevented trade for %s %s", symbol, timeframe)
        return
    lot, sl, tp_levels, _bem, regime = prep

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
        exposure_guard.record(symbol, timeframe, decision, confidence)
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
            regime=regime,
        )
        trade_cache.add((symbol, timeframe))
        alert_trade_opened(symbol, timeframe, decision, entry, sl, tp_levels[0])


def run_live_trade_manager() -> None:
    """Monitor open positions and adjust stops or close early."""
    positions = mt5.positions_get()
    history = {t["ticket"]: t for t in load_history()}
    if positions is None:
        return
    open_tickets = {p.ticket for p in positions}
    for sym, tf_map in list(executed_trades.items()):
        for tf, tkt in list(tf_map.items()):
            if tkt not in open_tickets:
                tf_map.pop(tf, None)
                trade_cache.discard((sym, tf))
                exposure_guard.remove(sym, tf)
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
                    update_trade(ticket, result="TP1 hit", hit="TP1")
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
                close_ts = datetime.utcnow().isoformat() + "Z"
                open_ts = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
                dur = (datetime.utcnow() - open_ts).total_seconds()
                pct = (
                    (price - rec["entry"]) / rec["entry"] * 100
                    if direction == "buy"
                    else (rec["entry"] - price) / rec["entry"] * 100
                )
                update_trade(
                    ticket,
                    result="closed_early",
                    closed_early=True,
                    exit=price,
                    close_time=close_ts,
                    duration=dur,
                    profit_pct=pct,
                    hit="closed_early",
                )
                update_strategy_score(rec["strategy"], "loss", regime=rec.get("regime", ""))
                executed_trades.get(pos.symbol, {}).pop(rec["timeframe"], None)
                trade_cache.discard((pos.symbol, rec["timeframe"]))
                exposure_guard.remove(pos.symbol, rec["timeframe"])
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
