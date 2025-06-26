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
) -> None:
    """Append a trade entry to the history log."""
    history = _load_history()
    timestamp = timestamp or datetime.utcnow().isoformat() + "Z"
    trade = {
        "symbol": symbol,
        "timeframe": timeframe,
        "strategy": strategy,
        "entry": entry,
        "sl": sl,
        "tp": tps,
        "result": result,
        "regime": regime,
        "exit": exit,
        "close_time": close_time,
        "duration": duration,
        "profit_pct": profit_pct,
        "net_profit_pct": net_profit_pct,
        "commission_usd": commission_usd,
        "swap_usd": swap_usd,
        "exit_reason": exit_reason,
        "hit": hit,
        "sl_moved": sl_moved,
        "closed_early": closed_early,
        "volume": volume,
        "ticket": ticket,
        "timestamp": timestamp,
        "trail_distance": trail_distance,
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
            if exit is not None:
                trade["exit"] = exit
            if close_time is not None:
                trade["close_time"] = close_time
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
                    win_condition = net_val > 0
                    outcome = "win" if win_condition else "loss"
                    update_strategy_score(
                        trade.get("strategy", ""),
                        outcome,
                        net_val,
                        regime=trade.get("regime", ""),
                    )
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
                    trade["duration"] = (close_ts - open_ts).total_seconds() / 60
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
