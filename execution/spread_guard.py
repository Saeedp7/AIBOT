from __future__ import annotations

"""Simple spread guard for scalping reliability."""

import MetaTrader5 as mt5

from config.manager import get_config

# Maximum allowed spread in points
MAX_SPREAD = float(get_config("MAX_SPREAD", 50.0))


def spread_within_limit(symbol: str) -> bool:
    """Return True if current spread for ``symbol`` is <= ``MAX_SPREAD``."""
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return False
    spread = abs(tick.ask - tick.bid)
    return spread <= MAX_SPREAD