from __future__ import annotations

import pandas as pd
from typing import Tuple

from risk_management.stop_loss_manager import determine_sl_tp
from risk_management.lot_sizing_module import calculate_lot_size
from risk_management.breakeven_manager import BreakEvenManager
from config.settings import SL_BUFFER_AFTER_TP1
from risk_management.daily_guard import DailyGuard
import MetaTrader5 as mt5
from utils.stop_level import enforce_min_sl_tp


def prepare_trade_parameters(
    *,
    symbol: str,
    strategy_name: str,
    direction: str,
    entry_price: float,
    market_data: pd.DataFrame,
    account_balance: float,
    risk_percent: float = 1.0,
    guard: DailyGuard,
) -> Tuple[float, float, list[float], BreakEvenManager, str] | None:
    """Compute lot size, SL/TP levels and breakeven manager after guard check.

    Returns ``None`` if ``guard`` disallows trading.
    """
    if not guard.can_trade():
        return None

    sl, tp_levels, regime = determine_sl_tp(
        strategy_name, entry_price, direction, market_data, symbol=symbol
    )
    info = mt5.symbol_info(symbol)
    if info:
        min_dist = getattr(info, "trade_stops_level", getattr(info, "stops_level", 0)) * info.point
        sl, tp_levels[0] = enforce_min_sl_tp(entry_price, sl, tp_levels[0], min_dist, direction)
        for i in range(1, len(tp_levels)):
            _, tp_levels[i] = enforce_min_sl_tp(entry_price, sl, tp_levels[i], min_dist, direction)
        digits = getattr(info, "digits", 2)
        sl = round(sl, digits)
        tp_levels = [round(t, digits) for t in tp_levels]
    lot = calculate_lot_size(
        balance=account_balance,
        sl_distance=abs(entry_price - sl),
        risk_percent=risk_percent,
        symbol=symbol,
        market_data=market_data,
    )
    
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(
        "Risk params for %s %s: lot=%s sl=%s tp1=%s",
        symbol,
        strategy_name,
        lot,
        sl,
        tp_levels[0] if tp_levels else None,
    )
    trail_dist = abs(tp_levels[0] - entry_price) if tp_levels else 0.0
    bem = BreakEvenManager(
        entry_price,
        direction,
        sl,
        tp_levels,
        sl_buffer=SL_BUFFER_AFTER_TP1,
        trail_distance=trail_dist,
    )
    return lot, sl, tp_levels, bem, regime