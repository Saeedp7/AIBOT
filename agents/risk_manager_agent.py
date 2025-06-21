from __future__ import annotations

from typing import Tuple

import MetaTrader5 as mt5


class RiskManagerAgent:
    """Perform pre-trade margin and duplication checks."""

    def validate_trade(self, symbol: str, lot: float) -> Tuple[bool, str]:
        info = mt5.account_info()
        if not info:
            return False, "account info unavailable"
        # simple margin estimate placeholder
        required = lot * 1000.0
        if info.margin_free is not None and info.margin_free < required:
            return False, "Insufficient margin"
        if mt5.positions_get(symbol=symbol):
            return False, "Position already open"
        return True, ""