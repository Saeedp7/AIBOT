"""Trade execution helpers."""

from __future__ import annotations

from typing import List

from execution.order_manager import execute_fake_order
from ai_engine.score_updater import load_asset_scores

class TradeExecutor:
    """Execute trades via order_manager or external API."""

    def execute(
        self,
        symbol: str,
        entry_price: float,
        lot: float,
        sl: float,
        tp_list: List[float] | None = None,
        *,
        strategy: str = "",
    ) -> int:
        """Execute order and return fake ticket id."""
        base_lot = lot
        scores = load_asset_scores()
        conf = float(scores.get(symbol, {}).get(strategy, 0.0))
        if conf > 1.2:
            lot = base_lot * 1.5
        elif conf < 0.3:
            lot = base_lot * 0.5
        execute_fake_order("buy", symbol, lot, entry_price, sl, tp_list)
        return 0
