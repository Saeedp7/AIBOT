"""Trade journal utilities for persistent trade history."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

from ai_engine.score_updater import update_strategy_score

HISTORY_PATH = "logs/trade_history.json"


def _load_history() -> List[Dict[str, Any]]:
    if not os.path.exists(HISTORY_PATH):
        return []
    try:
        with open(HISTORY_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(history: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(history, f, indent=2)


def record_trade(
    symbol: str,
    timeframe: str,
    entry: float,
    sl: float,
    tps: List[float],
    strategy: str,
    result: str,
    ticket: int,
    regime: str | None = None,
    exit: float | None = None,
    close_time: str | None = None,
    duration: float | None = None,
    entry_time: str | None = None,
    exit_time: str | None = None,
    duration_min: float | None = None,
    profit_pct: float | None = None,
    net_profit_pct: float | None = None,
    commission_usd: float | None = None,
    swap_usd: float | None = None,
    exit_reason: str | None = None,
    hit: str | None = None,
    sl_moved: bool = False,
    closed_early: bool = False,
    volume: float | None = None,
    trail_distance: float | None = None,
    timestamp: str | None = None,
    tp_index: int | None = None,
    *,
    pattern_detected: str | None = None,
    entry_zone: str | None = None,
    bias: str | None = None,
    session_tag: str | None = None,
    rr_ratio: float | None = None,
) -> None:
    """Append a trade entry to the history log."""
    history = _load_history()
    timestamp = timestamp or datetime.utcnow().isoformat() + "Z"
    entry_time = entry_time or timestamp
    exit_time = exit_time or close_time
    duration_min = duration_min or duration

    exit_price = exit
    commission = commission_usd
    swap = swap_usd

    if result and result.lower() != "open" and (exit is None or exit == 0.0):
        try:
            import MetaTrader5 as mt5  # type: ignore

            deals = getattr(mt5, "history_deals_get", lambda **_: None)(ticket=ticket)
        except Exception:
            deals = None
        if deals:
            exit_price = getattr(deals[-1], "price", exit_price)
            if commission is None:
                commission = -sum(getattr(d, "commission", 0.0) for d in deals)
            if swap is None:
                swap = -sum(getattr(d, "swap", 0.0) for d in deals)

    # ✅ fallback exit price if still missing
    if result and result.lower() != "open" and exit_price in (None, 0.0):
        exit_price = tps[-1] if result == "win" else sl

    direction = 1
    if tps:
        direction = 1 if tps[0] > entry else -1
    elif sl is not None:
        direction = 1 if sl < entry else -1

    calc_profit_pct = profit_pct
    calc_net_pct = net_profit_pct

    if result and result.lower() != "open" and exit_price not in (None, 0.0):
        diff = (exit_price - entry) * direction
        calc_profit_pct = diff / entry * 100
        if volume and commission is not None and swap is not None:
            charges = commission + swap
            calc_net_pct = calc_profit_pct - (charges / (entry * volume * 100000.0) * 100)
    trade = {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy": strategy,
        "entry": entry,
        "sl": sl,
        "tp": tps,
        "result": result,
        "regime": regime,
        "exit": exit_price,
        "close_time": close_time,
        "exit_time": exit_time,
        "duration": duration,
        "duration_min": duration_min,
        "profit_pct": calc_profit_pct,
        "net_profit_pct": calc_net_pct,
        "commission_usd": commission,
        "swap_usd": swap,
        "exit_reason": exit_reason,
        "hit": hit,
        "sl_moved": sl_moved,
        "closed_early": closed_early,
        "volume": volume,
        "ticket": ticket,
        "timestamp": timestamp,
        "entry_time": entry_time,
        "trail_distance": trail_distance,
        "pattern_detected": pattern_detected,
        "entry_zone": entry_zone,
        "bias": bias,
        "session_tag": session_tag,
        "rr_ratio": rr_ratio,
    }
    if regime is not None:
        trade["regime"] = regime
    if tp_index is not None:
        trade["tp_index"] = tp_index
    history.append(trade)
    _save_history(history)


def update_trade(
    ticket: int,
    *,
    exit: float | None = None,
    close_time: str | None = None,
    result: str | None = None,
    profit_pct: float | None = None,
    net_profit_pct: float | None = None,
    commission_usd: float | None = None,
    swap_usd: float | None = None,
    exit_reason: str | None = None,
    **updates: Any,
) -> None:
    """Update an existing trade entry by ticket."""
    history = _load_history()
    for trade in history:
        if trade.get("ticket") == ticket:
            net_val = 0.0
            if exit is not None and exit != 0.0:
                trade["exit"] = exit
            if close_time is not None:
                trade["close_time"] = close_time
                trade["exit_time"] = close_time
            if result is not None:
                trade["result"] = result
                if result.lower() != "open" and (
                    net_profit_pct is not None or trade.get("net_profit_pct") is not None
                ):
                    net_val = (
                        float(net_profit_pct)
                        if net_profit_pct is not None
                        else float(trade.get("net_profit_pct", 0.0))
                    )
            if net_val > 0:
                    outcome = "win"
            elif net_val < 0:
                    outcome = "loss"
            else:
                    outcome = None
            if outcome:
                        update_strategy_score(
                            trade.get("strategy", ""),
                            outcome,
                            net_val,
                            regime=trade.get("regime", ""),
                            symbol=trade.get("symbol", ""),
                            timeframe=trade.get("timeframe", ""),
                        )
            # Fetch exit details if missing and trade has closed
            if result and result.lower() != "open" and trade.get("exit") in (None, 0.0):
                try:
                    import MetaTrader5 as mt5  # type: ignore

                    deals = getattr(mt5, "history_deals_get", lambda **_: None)(ticket=ticket)
                except Exception:
                    deals = None
                if deals:
                    trade["exit"] = getattr(deals[-1], "price", trade.get("exit"))
                    if commission_usd is None:
                        commission_usd = -sum(getattr(d, "commission", 0.0) for d in deals)
                    if swap_usd is None:
                        swap_usd = -sum(getattr(d, "swap", 0.0) for d in deals)

            if profit_pct is None and trade.get("exit") not in (None, 0.0):
                direction = 1
                tps = trade.get("tp", [])
                if tps:
                    direction = 1 if tps[0] > trade["entry"] else -1
                elif trade.get("sl") is not None:
                    direction = 1 if trade["sl"] < trade["entry"] else -1
                diff = (float(trade["exit"]) - float(trade["entry"])) * direction
                profit_pct = diff / float(trade["entry"]) * 100
            if net_profit_pct is None and profit_pct is not None and commission_usd is not None and swap_usd is not None and trade.get("volume"):
                charges = commission_usd + swap_usd
                vol = float(trade.get("volume", 0.0))
                net_profit_pct = profit_pct - (charges / (float(trade["entry"]) * vol * 100000.0) * 100)
            if profit_pct is not None:
                trade["profit_pct"] = profit_pct
            if net_profit_pct is not None:
                trade["net_profit_pct"] = net_profit_pct
            if commission_usd is not None:
                trade["commission_usd"] = commission_usd
            if swap_usd is not None:
                trade["swap_usd"] = swap_usd
            if exit_reason is not None:
                trade["exit_reason"] = exit_reason

            if close_time and not trade.get("duration") and trade.get("timestamp"):
                try:
                    open_ts = datetime.fromisoformat(trade["timestamp"].replace("Z", "+00:00"))
                    close_ts = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
                    dur_min = (close_ts - open_ts).total_seconds() / 60
                    trade["duration"] = dur_min
                    trade["duration_min"] = dur_min
                except Exception:
                    pass

            if commission_usd is None and trade.get("commission_usd") is None and trade.get("symbol"):
                from risk_management.commission_calculator import estimate_commission
                lot = updates.get("volume", 0.0)
                try:
                    trade["commission_usd"] = estimate_commission(trade["symbol"], lot)
                except Exception:
                    trade["commission_usd"] = 0.0
            trade.update(updates)
            break
    _save_history(history)


def load_history() -> List[Dict[str, Any]]:
    """Public helper to load full trade history."""
    return _load_history()
