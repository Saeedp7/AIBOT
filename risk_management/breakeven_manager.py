# risk_management/breakeven_manager.py
"""Utility to adjust stop loss as take profit targets are hit."""

from typing import List


class BreakEvenManager:
    """Manage stop loss adjustments after partial take profits."""

    def __init__(self, entry_price: float, direction: str,
                 stop_loss: float, tp_levels: List[float]):
        self.entry_price = entry_price
        self.direction = direction.lower()
        self.stop_loss = stop_loss
        self.tp_levels = tp_levels
        self._reached = set()

    def update_stop_loss(self, current_price: float) -> float:
        """Update stop loss if a new TP level has been reached."""
        if self.direction not in {"buy", "sell"}:
            raise ValueError("direction must be 'buy' or 'sell'")

        for i, tp in enumerate(self.tp_levels):
            if i in self._reached:
                continue

            hit_tp = current_price >= tp if self.direction == "buy" else current_price <= tp
            if hit_tp:
                self._reached.add(i)
                if i == 0:
                    self.stop_loss = self.entry_price
                else:
                    self.stop_loss = self.tp_levels[i - 1]
        return self.stop_loss