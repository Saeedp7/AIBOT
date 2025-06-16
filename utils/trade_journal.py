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
    hit: str | None = None,
    sl_moved: bool = False,
    closed_early: bool = False,
    timestamp: str | None = None,
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
        "hit": hit,
        "sl_moved": sl_moved,
        "closed_early": closed_early,
        "ticket": ticket,
        "timestamp": timestamp,
    }
    if regime is not None:
        trade["regime"] = regime
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
                if result.lower() != "open":
                    hit = str(result).lower()
                    net_val = net_profit_pct if net_profit_pct is not None else trade.get("net_profit_pct", 0)
                    win_condition = (float(net_val) > 0) or hit.startswith("tp")
                    outcome = "win" if win_condition else "loss"
                    update_strategy_score(
                        trade.get("strategy", ""),
                        outcome,
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
            trade.update(updates)
            break
    _save_history(history)


def load_history() -> List[Dict[str, Any]]:
    """Public helper to load full trade history."""
    return _load_history()
