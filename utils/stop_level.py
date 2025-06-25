import logging
from typing import Tuple, Optional

import MetaTrader5 as mt5

from config.manager import get_config

STOP_LEVEL_BUFFER_PCT = float(get_config("STOP_LEVEL_BUFFER_PCT", 0))

def enforce_min_stop_distance(
    symbol: str,
    entry_price: float,
    sl: float,
    tp: Optional[float],
    direction: str,
) -> Tuple[float, Optional[float], bool]:
    """Ensure SL and TP meet broker stop level requirements.

    Returns tuple of (adjusted_sl, adjusted_tp, is_valid).
    """
    info = mt5.symbol_info(symbol)
    if not info:
        logging.warning(f"Could not retrieve SymbolInfo for {symbol}")
        return sl, tp, True

    trade_stop_points = getattr(info, "trade_stops_level", getattr(info, "stops_level", 0))
    min_distance = trade_stop_points * info.point
    min_distance *= 1 + (STOP_LEVEL_BUFFER_PCT / 100)
    digits = getattr(info, "digits", 2)

    adjusted = False
    if abs(entry_price - sl) < min_distance:
        orig = sl
        sl = entry_price - min_distance if direction == "buy" else entry_price + min_distance
        sl = round(sl, digits)
        logging.info(f"Adjusted SL for {symbol}: {orig} -> {sl} to satisfy minimum stop level")
        adjusted = True

    if tp is not None and abs(entry_price - tp) < min_distance:
        orig = tp
        tp = entry_price + min_distance if direction == "buy" else entry_price - min_distance
        tp = round(tp, digits)
        logging.info(f"Adjusted TP for {symbol}: {orig} -> {tp} to satisfy minimum stop level")
        adjusted = True

    if abs(entry_price - sl) < min_distance or (
        tp is not None and abs(entry_price - tp) < min_distance
    ):
        logging.warning(
            f"Invalid stop levels for {symbol}. SL/TP too close to price even after adjustment."
        )
        return sl, tp, False

    return sl, tp, True