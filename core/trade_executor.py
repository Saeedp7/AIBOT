"""Trade execution helpers."""

from __future__ import annotations

from typing import List

import os
from execution.order_manager import execute_fake_order


class TradeExecutor:
    """Execute trades via order_manager or MetaTrader5."""

    def execute(
        self,
        direction: str,
        symbol: str,
        entry_price: float,
        lot: float,
        sl: float,
        tp_list: List[float] | None = None,
    ) -> int:
        """Execute order and return ticket id."""
        live = os.getenv("LIVE_MODE", "false").lower() == "true"
        if not live:
            execute_fake_order(direction, symbol, lot, entry_price, sl, tp_list)
            return 0

        try:
            import MetaTrader5 as mt5  # type: ignore
        except Exception:  # pragma: no cover - MT5 missing
            execute_fake_order(direction, symbol, lot, entry_price, sl, tp_list)
            return 0

        tick = mt5.symbol_info_tick(symbol)
        if tick and entry_price <= 0:
            entry_price = tick.ask if direction == "buy" else tick.bid

        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL,
            "price": entry_price,
            "sl": sl,
            "tp": tp_list[0] if tp_list else 0.0,
            "deviation": 20,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        res = mt5.order_send(req)
        ticket = getattr(res, "order", -1) if res else -1
        return ticket
