"""Trade execution helpers."""

from __future__ import annotations

from typing import List

from execution.order_manager import execute_fake_order


class TradeExecutor:
    """Execute trades via order_manager or external API."""

    def execute(
        self,
        symbol: str,
        entry_price: float,
        lot: float,
        sl: float,
        tp_list: List[float] | None = None,
    ) -> int:
        """Execute order and return fake ticket id."""
        execute_fake_order("buy", symbol, lot, entry_price, sl, tp_list)
        return 0
