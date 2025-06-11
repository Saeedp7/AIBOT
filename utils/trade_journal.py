"""Trade journal utilities for persistent trade history."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

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
            if profit_pct is not None:
                trade["profit_pct"] = profit_pct
            trade.update(updates)
            break
    _save_history(history)


def load_history() -> List[Dict[str, Any]]:
    """Public helper to load full trade history."""
    return _load_history()
