# PATCHED: live/scheduler_loop.py (now uses regime-aware multi-TP SL/TP logic + updates AI memory)

from __future__ import annotations


import time
import threading
from datetime import datetime, date, timedelta
import argparse
import logging
import os
import json
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
PARTIAL_CLOSE_RATIOS = [
    float(x)
    for x in get_config("PARTIAL_CLOSE_RATIOS", "0.33,0.33,0.34").split(",")
    if x
]
STOP_LEVEL_BUFFER_PCT = float(get_config("STOP_LEVEL_BUFFER_PCT", 0))
from ai_engine.parameter_optimizer import load_strategy_thresholds
from config.settings import (
    DEFAULT_CONFIDENCE_THRESHOLDS,
    MIN_RISK_SCALE,
    DEFAULT_ALLOWED_REGIMES,
    SL_BUFFER_AFTER_TP1,
)
from data.chart_data_handler import load_multi_ohlcv
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators
from strategies.strategy_selector import StrategySelector
from agents.strategy_selector_agent import StrategySelectorAgent
from agents.risk_manager_agent import RiskManagerAgent
from agents.trade_monitor_agent import TradeMonitorAgent
from ai_engine.strategy_selector import load_scores
from ai_engine.score_updater import update_strategy_score, update_ai_from_trade
from risk_management.core import prepare_trade_parameters
from risk_management.commission_calculator import estimate_commission, estimate_swap
from risk_management.daily_guard import DailyGuard
from risk_management.exposure_guard import ExposureGuard
from connectors.mt5_connector import get_account_info
from utils.trade_journal import record_trade, update_trade, load_history, load_history_dict
from utils.logger import log_trade_action
from risk_management.breakeven_manager import BreakEvenManager
from ai_engine.strategy_score_manager import recover_old_scores
from core.trade_engine import execute_trade
from monitoring.alert_manager import (
    alert_sl_moved,
    alert_trade_closed,
    alert_daily_guard,
    send_telegram_alert,
    retry_failed_alerts,
)
from execution.spread_guard import spread_within_limit
from risk_management.session_guard import session_allowed
from utils.time_utils import session_risk_multiplier
from recovery.restart_manager import recover_state
import MetaTrader5 as mt5
from utils.market_status import is_market_open
from utils.stop_level import enforce_min_stop_distance
from strategies.smc_strategy import SMCStrategy
from risk_management.lot_sizing_module import calculate_lot_size
from strategy_components.session_filter import (
    in_killzone,
    LONDON_OPEN,
    NEWYORK_OPEN,
    NEWYORK_PM,
)

logger = logging.getLogger("scheduler")



def get_confidence_threshold(symbol: str, timeframe: str, regime: str, strategy_name: str) -> float:
    """Return confidence threshold for a trade context."""
    overrides = load_strategy_thresholds()
    if strategy_name in overrides:
        try:
            return float(overrides[strategy_name])
        except (TypeError, ValueError):
            pass
    return float(DEFAULT_CONFIDENCE_THRESHOLDS.get(regime, 0.3))


def scale_risk_by_confidence(confidence: float, threshold: float) -> float:
    """Return position size multiplier based on confidence level."""
    if threshold <= 0:
        return 1.0
    if confidence >= threshold:
        return 1.0
    scale = confidence / threshold
    return max(MIN_RISK_SCALE, round(scale, 2))


def _session_label(ts: datetime) -> str:
    t = ts.time()
    if LONDON_OPEN[0] <= t <= LONDON_OPEN[1]:
        return "London"
    if NEWYORK_OPEN[0] <= t <= NEWYORK_OPEN[1]:
        return "NYO"
    if NEWYORK_PM[0] <= t <= NEWYORK_PM[1]:
        return "PM"
    return "Off"

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live trading scheduler loop")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--silent", action="store_true", help="Suppress info logging")
    parser.add_argument(
        "--force-trade",
        action="store_true",
        help="Override risk/session guards",
    )
    args = parser.parse_args()
    if os.getenv("FORCE_TRADE", "false").lower() == "true":
        args.force_trade = True
    return args

daily_guard = DailyGuard(
    loss_limit_percent=DAILY_LOSS_LIMIT_PERCENT,
    max_trades=MAX_TRADES_PER_DAY,
)

daily_guard_alert_sent = False
daily_guard_trigger_date: date | None = None

# Track currently open trades per symbol/timeframe
active_trades: dict[tuple[str, str], bool] = {}
strategy_selector_agent = StrategySelectorAgent(StrategySelector().strategies)

# Expand TIMEFRAMES to include each strategy's preferred timeframe
strategy_tfs = {getattr(s, "preferred_tf", "M15") for s in strategy_selector_agent.strategies}
TIMEFRAMES = sorted(set(TIMEFRAMES) | strategy_tfs)
ACTIVE_SYMBOLS_TIMEFRAMES = {s: TIMEFRAMES for s in SYMBOLS}

risk_manager_agent = RiskManagerAgent()
smc_strategy = SMCStrategy()

# Restore state from previous session if possible
executed_trades, exposure_guard = recover_state()
for sym, tf_map in executed_trades.items():
    for tf in tf_map:
        active_trades[(sym, tf)] = True

# Cache OHLCV and indicator data per symbol/timeframe
ohlcv_cache: Dict[Tuple[str, str], pd.DataFrame] = {}
indicator_cache: Dict[Tuple[str, str], pd.DataFrame] = {}

def refresh_active_symbols() -> None:
    """Update ACTIVE_SYMBOLS_TIMEFRAMES based on is_market_open()."""
    global ACTIVE_SYMBOLS_TIMEFRAMES
    active = [s for s in SYMBOLS if is_market_open(s)]
    ACTIVE_SYMBOLS_TIMEFRAMES = {s: TIMEFRAMES for s in active}

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



def process_symbol_timeframe(symbol: str, timeframe: str, *, force_trade: bool = False) -> None:
    logger.info(f"Checking symbol: {symbol}")
    if not is_market_open(symbol) and not force_trade:
        logger.warning(
            f"[SKIP] Trade skipped: {symbol} {timeframe} - Reason: Market is Closed"
        )
        return
    today = date.today()
    global daily_guard_alert_sent, daily_guard_trigger_date
    if daily_guard_alert_sent and daily_guard_trigger_date == today:
        logger.info(f"[SKIP] Bot paused due to Daily Guard for {today}")
        return
    if not force_trade and daily_guard.hit_limits():
        if not daily_guard_alert_sent or daily_guard_trigger_date != today:
            alert_daily_guard(
                f"\u274c Daily limit hit. Bot halted until {today + timedelta(days=1)}"
            )
            daily_guard_alert_sent = True
            daily_guard_trigger_date = today
        return

    # Ensure active_trades reflects actual open positions
    if not mt5.positions_get(symbol=symbol):
        if active_trades.pop((symbol, timeframe), None) is not None:
            logger.debug(f"Cleaning up stale trade slot: {symbol} {timeframe}")

    if (symbol, timeframe) in active_trades and not force_trade:
        logger.warning(
            f"[SKIP] Trade skipped: {symbol} {timeframe} - Reason: Max open trades"
        )
        return
    if executed_trades.get(symbol, {}).get(timeframe) and not force_trade:
        logger.warning(
            f"[SKIP] Trade skipped: {symbol} {timeframe} - Reason: Max open trades"
        )
        return
    df = indicator_cache.get((symbol, timeframe))
    if df is None or df.empty:
        logger.warning(
            f"[SKIP] Trade skipped: {symbol} {timeframe} - Reason: Missing market data"
        )
        return

    smc_trade = smc_strategy.generate_signal(df.copy())
    if smc_trade and not force_trade:
        logger.info(
            f"[SMC SIGNAL] {symbol} {timeframe} → {smc_trade['direction'].upper()}"
        )
        acct = mt5.account_info()
        lot = calculate_lot_size(
            acct.balance,
            abs(smc_trade["entry"] - smc_trade["sl"]),
            MAX_RISK_PER_TRADE * 100,
            symbol,
            df,
        )
        tp_levels = [
            smc_trade.get("tp1"),
            smc_trade.get("tp2"),
            smc_trade.get("tp3"),
        ]
        tp_levels = [tp for tp in tp_levels if tp]
        if not tp_levels:
            logger.warning("SMC trade missing TP levels")
            return
        tickets: list[int] = []
        for idx, ratio in enumerate(PARTIAL_CLOSE_RATIOS[: len(tp_levels)]):
            sub_lot = round(max(lot * ratio, 0.01), 2)
            tkt = execute_trade(
                smc_trade["direction"],
                symbol,
                sub_lot,
                smc_trade["sl"],
                tp_levels[idx],
                magic_offset=idx,
            )
            if tkt:
                tickets.append(tkt)
                record_trade(
                    symbol=symbol,
                    timeframe=timeframe,
                    entry=smc_trade["entry"],
                    sl=smc_trade["sl"],
                    tps=tp_levels,
                    strategy="SMCStrategy",
                    result="open",
                    ticket=tkt,
                    volume=sub_lot,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    regime=smc_trade.get("regime"),
                    tp_index=idx,
                    pattern_detected=smc_trade.get("label", "SMC"),
                    entry_zone="OB" if smc_trade.get("label", "").startswith("SMC") else None,
                    bias=smc_trade.get("regime"),
                    session_tag=_session_label(datetime.utcnow()),
                    rr_ratio=smc_trade.get("rr_ratio", 0.0),
                )
        active_trades[(symbol, timeframe)] = True
        return

    decision, best_strat, strat_tf, market_regime = strategy_selector_agent.select(symbol, timeframe)
    if decision not in ("buy", "sell") or not best_strat:
        logger.warning(
            f"[SKIP] Trade skipped: {symbol} {timeframe} - Reason: No valid signal"
        )
        return
    
    logger.info(
        f"[SIGNAL GENERATED] {best_strat} | {symbol} {strat_tf} → {decision.upper()}"
    )
    # Regime enforcement: block trades if strategy not allowed in detected regime
    strat_obj = next(
        (s for s in strategy_selector_agent.strategies if s.__class__.__name__ == best_strat),
        None,
    )
    if strat_obj is not None and hasattr(strat_obj, "allowed_regimes"):
        allowed = strat_obj.allowed_regimes()
    elif strat_obj is not None:
        allowed = list(getattr(strat_obj, "ALLOWED_REGIMES", DEFAULT_ALLOWED_REGIMES))
    else:
        allowed = list(DEFAULT_ALLOWED_REGIMES)
    if market_regime not in allowed:
        log_trade_action(
            f"Skipping trade for {symbol} {timeframe}: regime {market_regime} not allowed for {best_strat}"
        )
        logger.warning(
            f"[SKIP] Trade skipped: {symbol} {timeframe} - Reason: Regime {market_regime} not allowed"
        )
        return



    if not spread_within_limit(symbol):
        logger.warning(
            f"[SKIP] Trade skipped: {symbol} {timeframe} - Reason: Spread too high"
        )
        return


    tick = mt5.symbol_info_tick(symbol)
    if tick:
        entry = tick.ask if decision == "buy" else tick.bid
    else:
        entry = df["close"].iloc[-1]
    scores = load_scores()
    metrics = scores.get(best_strat, {})
    confidence = (
        float(metrics.get("recent_score", 0.0))
        * float(metrics.get("regime_fit", 0.0))
        * float(metrics.get("win_rate", 0.0))
    )
    threshold = get_confidence_threshold(symbol, timeframe, market_regime, best_strat)
    scale = scale_risk_by_confidence(confidence, threshold)
    log_trade_action(
        f"Confidence {confidence:.4f} th={threshold:.2f} scale={scale:.2f} for {symbol} {timeframe} using {best_strat}"
    )
    if scale < 1.0:
        logger.info(
            "Scaling trade risk for %s %s to %.2f due to confidence %.4f",
            symbol,
            timeframe,
            scale,
            confidence,
        )

    if not force_trade and not exposure_guard.allow(symbol, timeframe, decision, confidence):
        log_trade_action(
            f"🚫 Exposure guard blocked trade: {symbol} {timeframe} {decision}"
        )
        logger.warning(
            f"[SKIP] Trade skipped: {symbol} {timeframe} - Reason: Exposure guard"
        )
        return
    if not session_allowed(symbol) and not force_trade:
        logger.warning(
            f"[SKIP] Trade skipped: {symbol} {timeframe} - Reason: Session guard"
        )
        return
    
    risk_multiplier = session_risk_multiplier(datetime.utcnow())
    if force_trade:
        risk_multiplier = 1.0
    else:
        risk_multiplier *= scale
        if risk_multiplier < 1.0:
            logger.info(
                "Low session active — applying reduced lot size multiplier: %s",
                risk_multiplier,
            )
    acct = mt5.account_info()
    prep = prepare_trade_parameters(
        symbol=symbol,
        strategy_name=best_strat,
        direction=decision,
        entry_price=entry,
        market_data=df,
        account_balance=acct.balance,
        risk_percent=MAX_RISK_PER_TRADE * 100 * risk_multiplier,
        guard=daily_guard,
    )
    if not prep and force_trade:
        prep = prepare_trade_parameters(
            symbol=symbol,
            strategy_name=best_strat,
            direction=decision,
            entry_price=entry,
            market_data=df,
            account_balance=acct.balance,
            risk_percent=MAX_RISK_PER_TRADE * 100 * risk_multiplier,
            guard=DailyGuard(loss_limit_percent=10000.0, max_trades=1000000),
        )
    if not prep:
        logger.info("Risk guard prevented trade for %s %s", symbol, timeframe)
        return
    lot, sl, tp_levels, _bem, regime = prep
    ok, reason = risk_manager_agent.validate_trade(symbol, lot)
    if not ok:
        logger.warning(
            f"[SKIP] Trade skipped: {symbol} {timeframe} - Reason: {reason}"
        )
        return
    commission = estimate_commission(symbol, lot)
    direction_mult = 1 if decision == "buy" else -1
    print(tp_levels)
    tp_slice = tp_levels[:3]
    # Keep original sl/tp from strategy logic

    # Slightly widen SL to absorb commission only
    sl_diff = abs(entry - sl)
    sl_adjusted = sl_diff + (commission / (lot * 100000.0))
    sl = round(entry - direction_mult * sl_adjusted, 2)
    
    logger.info(f"Estimated commission for {symbol}: ${commission:.2f}")
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
    logger.debug(
        "Order params: symbol=%s tf=%s direction=%s lot=%.2f sl=%.5f tp1=%.5f",
        symbol,
        timeframe,
        decision,
        lot,
        sl,
        tp_levels[0],
    )
    trail_dist = _bem.trail_distance
    tickets: list[int] = []
    for idx, ratio in enumerate(PARTIAL_CLOSE_RATIOS[:3]):
        sub_lot_raw = lot * ratio
        sub_lot = round(max(sub_lot_raw, 0.01), 2)
        if sub_lot <= 0:
            continue
        tp_val = tp_levels[idx] if idx < len(tp_levels) else tp_levels[-1]
        assert tp_val in tp_levels, f"Mismatch in TP levels: {tp_val} not in {tp_levels}"
        print(tp_val)
        tkt = execute_trade(
            decision,
            symbol,
            sub_lot,
            sl,
            tp=tp_val,
            magic_offset=idx,
        )
        if tkt:
            tickets.append(tkt)
            record_trade(
                symbol=symbol,
                timeframe=timeframe,
                entry=entry,
                sl=sl,
                tps=tp_levels,
                strategy=best_strat,
                result="open",
                ticket=tkt,
                volume=sub_lot,
                timestamp=datetime.utcnow().isoformat() + "Z",
                regime=regime,
                tp_index=idx,
                trail_distance=trail_dist,
            )
            monitor = TradeMonitorAgent(tkt, symbol, timeframe, best_strat, regime)
            threading.Thread(target=monitor.wait_and_score, daemon=True).start()
            tp_info = ", ".join([f"TP{i+1}: {tp}" for i, tp in enumerate(tp_levels[:3])])
            alert_msg = (
                f"\u2705 Trade Executed\n"
                f"Symbol: {symbol}\n"
                f"Timeframe: {timeframe}\n"
                f"Strategy: {best_strat}\n"
                f"Regime: {regime}\n"
                f"Direction: {decision.upper()}\n"
                f"Entry: {entry}\n"
                f"SL: {sl}\n"
                f"{tp_info}\n"
                f"Lot: {sub_lot}\n"
                f"Ticket: {tkt}"
            )
            send_telegram_alert(alert_msg)

    if tickets:
        from execution.multi_tp_manager import register_group

        register_group(
            tickets,
            symbol,
            decision,
            entry,
            sl,
            tp_slice,
            SL_BUFFER_AFTER_TP1,
        )
        daily_guard.record_trade(0)
        exposure_guard.record(symbol, timeframe, decision, confidence)
        executed_trades.setdefault(symbol, {}).setdefault(timeframe, []).extend(tickets)
        active_trades[(symbol, timeframe)] = True
        logger.info(
            f"[EXECUTED] Opened multi-TP orders: {symbol} {timeframe} tickets={tickets}"
        )
    else:
        logger.error(
            f"[FAIL] Trade failed for {symbol} {timeframe}"
        )



def run_live_trade_manager() -> None:
    """Monitor open positions and adjust stops or close early."""
    positions = mt5.positions_get()
    history = load_history_dict()
    if positions is None:
        return
    open_tickets = {p.ticket for p in positions}
    for sym, tf_map in list(executed_trades.items()):
        for tf, tickets in list(tf_map.items()):
            remaining = [t for t in tickets if t in open_tickets]
            if remaining:
                tf_map[tf] = remaining
            else:
                tf_map.pop(tf, None)
                active_trades.pop((sym, tf), None)
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
        reached = set(rec.get("reached_tps", []))
        prev_reached = set(reached)
        # Check TP hits first so SL can be moved after
        tps = rec.get("tp", [])
        initial_vol = rec.get("volume", pos.volume)
        for i, tp in enumerate(tps):
            flag = f"tp{i + 1}_hit"
            if rec.get(flag):
                continue
            hit_tp = price >= tp if direction == "buy" else price <= tp
            if not hit_tp:
                continue
            log_trade_action(
                f"\u2705 TP{i + 1} hit for {pos.symbol} {rec['timeframe']} @ {price}"
            )
            update_trade(
                ticket,
                **{flag: True},
                hit=f"TP{i + 1}",
                reached_tps=list(reached | {i}),
            )
            rec[flag] = True
            reached.add(i)
            rec["reached_tps"] = list(reached)
            if i == 0 and rec.get("result") == "open":
                update_trade(ticket, result="TP1 hit", hit="TP1")
                rec["result"] = "TP1 hit"
                rec["tp1_hit"] = True
            break

        bem = BreakEvenManager(
            rec["entry"],
            direction,
            pos.sl,
            rec.get("tp", []),
            prev_reached,
            symbol=pos.symbol,
            lot=pos.volume,
            precision=getattr(mt5.symbol_info(pos.symbol), "digits", 2),
            trail_distance=rec.get("trail_distance", 0.0),
        )
        new_sl = bem.update_stop_loss(price)
        reached.update(bem.reached_tps)
        rec["reached_tps"] = list(reached)
        if new_sl != pos.sl:
            req = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": new_sl,
                "tp": pos.tp,
            }
            logger.debug("Adjusting SL/TP: %s", req)
            res = mt5.order_send(req)
            logger.debug(
                "Modify retcode=%s comment=%s",
                getattr(res, "retcode", None),
                getattr(res, "comment", ""),
            )
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                reason = "TP1" if 0 in bem.reached_tps and 0 not in prev_reached else "TP2" if 1 in bem.reached_tps and 1 not in prev_reached else "manual"
                log_trade_action(
                    f"[INFO] SL moved after {reason}: {pos.symbol} @ {price:.2f} → New SL: {new_sl:.2f} (Entry: {rec['entry']})"
                )
                update_trade(
                    ticket,
                    sl=new_sl,
                    sl_moved=True,
                    reached_tps=list(bem.reached_tps),
                )
                alert_sl_moved(pos.symbol, rec["timeframe"], new_sl)
        # simple reversal check only after any TP hit
        tp_hit_flag = any(
            rec.get(k)
            for k in ("tp1_hit", "tp2_hit", "tp3_hit")
        )
        if tp_hit_flag:
            if direction == "buy" and price < rec["entry"] - (rec["entry"] - rec["sl"]):
                close_type = mt5.ORDER_TYPE_SELL
            elif direction == "sell" and price > rec["entry"] + (rec["sl"] - rec["entry"]):
                close_type = mt5.ORDER_TYPE_BUY
            else:
                close_type = None
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
                time.sleep(1)
                confirm = mt5.positions_get(ticket=ticket)
                if confirm:
                    logger.warning("Close order sent but position still open %s", ticket)
                    continue
                log_trade_action(
                    f"Trade closed early on trend reversal: {pos.symbol} {rec['timeframe']}"
                )
                close_ts = datetime.utcnow().isoformat() + "Z"
                open_ts = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
                dur = (datetime.utcnow() - open_ts).total_seconds() / 60
                gross_pct = (
                    (price - rec["entry"]) / rec["entry"] * 100
                    if direction == "buy"
                    else (rec["entry"] - price) / rec["entry"] * 100
                )
                commission = estimate_commission(pos.symbol, pos.volume)
                swap = estimate_swap(pos.symbol, pos.volume, direction)
                net_pct = gross_pct - (
                    (commission + swap) / (rec["entry"] * pos.volume * 100000.0)
                ) * 100
                update_trade(
                    ticket,
                    result="closed_early",
                    closed_early=True,
                    exit=price,
                    close_time=close_ts,
                    duration=dur,
                    profit_pct=gross_pct,
                    net_profit_pct=net_pct,
                    commission_usd=commission,
                    swap_usd=swap,
                    hit="closed_early",
                    exit_reason="early_exit",
                )
                lst = executed_trades.get(pos.symbol, {}).get(rec["timeframe"], [])
                if ticket in lst:
                    lst.remove(ticket)
                if not lst:
                    executed_trades.get(pos.symbol, {}).pop(rec["timeframe"], None)
                active_trades.pop((pos.symbol, rec["timeframe"]), None)
                exposure_guard.remove(pos.symbol, rec["timeframe"])
                alert_trade_closed(pos.symbol, rec["timeframe"], "closed_early")
                send_telegram_alert(
                    f"\u2705 Trade {ticket} closed early at {price} (Net: {net_pct:+.2f}%)"
                )
                update_ai_from_trade(
                    ticket=ticket,
                    result="closed_early",
                    strategy=rec.get("strategy", ""),
                    regime=rec.get("regime", ""),
                    symbol=pos.symbol,
                    timeframe=rec["timeframe"],
                    net_profit_pct=net_pct,
                    tp_hits=rec.get("reached_tps", []),
                )


def scheduler_loop(args: argparse.Namespace) -> None:
    level = logging.DEBUG if args.debug else (logging.ERROR if args.silent else logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")
    while True:
        print("🔁 Loop is running...")
        recover_old_scores()
        global daily_guard_alert_sent, daily_guard_trigger_date
        if daily_guard_trigger_date and date.today() != daily_guard_trigger_date:
            daily_guard_alert_sent = False
            daily_guard_trigger_date = None
            logger.info("[RESET] Daily Guard reset for new day")
        if not mt5.initialize():
            logger.error("Failed to initialize MT5")
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue
        try:
            refresh_active_symbols()
            if not ACTIVE_SYMBOLS_TIMEFRAMES:
                logger.info("No markets open. Sleeping...")
                time.sleep(3600)
                continue
            run_live_trade_manager()
            retry_failed_alerts()
            for symbol, tfs in ACTIVE_SYMBOLS_TIMEFRAMES.items():
                for tf in tfs:
                    refresh_data(symbol, tf)
                    process_symbol_timeframe(symbol, tf, force_trade=args.force_trade)
        finally:
            mt5.shutdown()
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    scheduler_loop(_parse_args())
