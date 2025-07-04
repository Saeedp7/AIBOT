"""Utility helpers for determining market availability."""

from __future__ import annotations

from time import time as _time
import MetaTrader5 as mt5

def is_market_open(symbol: str, max_tick_age: int = 300) -> bool:
    """Return ``True`` if MT5 reports ``symbol`` is tradeable and active."""
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)

    if not info or not getattr(info, "visible", True):
        return False

    full_mode = getattr(mt5, "SYMBOL_TRADE_MODE_FULL", None)
    if full_mode is not None and info.trade_mode not in (full_mode,):
        return False

    if not tick or tick.bid <= 0 or tick.ask <= 0:
        return False

    tick_time = getattr(tick, "time", None)
    if tick_time is None:
        return False

    if _time() - tick_time > max_tick_age:
        return False

    return True
