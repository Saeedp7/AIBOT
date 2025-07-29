"""Crash recovery utilities for live trading."""

from __future__ import annotations

import MetaTrader5 as mt5

from utils.trade_journal import load_history
from risk_management.exposure_guard import ExposureGuard


def recover_state():
    """Restore executed trades and exposure guard from MT5 and history."""
    executed: dict[str, dict[str, list[int]]] = {}
    exposure = ExposureGuard()

    if not hasattr(mt5, "initialize") or not mt5.initialize():
        return executed, exposure

    positions = getattr(mt5, "positions_get", lambda: None)()
    raw_history = load_history()
    history: dict[int, dict] = {}
    for t in raw_history:
        if not isinstance(t, dict):
            continue
        result = str(t.get("result", "")).lower()
        if result != "open":
            continue
        ticket = t.get("ticket")
        if isinstance(ticket, list):
            ticket = ticket[0] if ticket else None
        if isinstance(ticket, int):
            history[ticket] = t
    if positions:
        for pos in positions:
            ticket = pos.ticket
            symbol = pos.symbol
            direction = "buy" if pos.type == mt5.POSITION_TYPE_BUY else "sell"
            rec = history.get(ticket)
            timeframe = rec.get("timeframe") if rec else ""
            executed.setdefault(symbol, {}).setdefault(timeframe, []).append(ticket)
            exposure.record(symbol, timeframe, direction, 1.0)
    mt5.shutdown()
    return executed, exposure