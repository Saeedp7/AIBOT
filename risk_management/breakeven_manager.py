# risk_management/breakeven_manager.py
"""Utility to adjust stop loss as take profit targets are hit."""

from typing import List
from config.settings import SL_BUFFER_AFTER_TP1

class BreakEvenManager:
    """Manage stop loss adjustments after partial take profits."""

    def __init__(
        self,
        entry_price: float,
        direction: str,
        stop_loss: float,
        tp_levels: List[float],
        reached: set[int] | None = None,
        *,
        symbol: str | None = None,
        lot: float = 0.0,
        precision: int = 2,
        sl_buffer: float = SL_BUFFER_AFTER_TP1,
    ) -> None:
        self.entry_price = entry_price
        self.entry = entry_price
        self.direction = direction.lower()
        self.stop_loss = stop_loss
        self.sl = stop_loss
        self.tp_levels = tp_levels
        self.symbol = symbol or ""
        self.lot = lot
        self.precision = precision
        self.sl_buffer = sl_buffer
        # Track which TP levels have been reached already
        self._reached = set(reached) if reached else set()
    @property
    def reached_tps(self) -> set[int]:
        """Return a copy of reached TP level indexes."""
        return set(self._reached)
    
    def update_stop_loss(self, current_price: float) -> float:
        """Update stop loss if a new TP level has been reached."""
        if self.direction not in {"buy", "sell"}:
            raise ValueError("direction must be 'buy' or 'sell'")

        if not self.tp_levels or self.entry is None or self.sl is None:
            return self.sl

         # Handle TP1 move
        if 0 not in self._reached:
            hit_tp1 = (
                current_price >= self.tp_levels[0]
                if self.direction == "buy"
                else current_price <= self.tp_levels[0]
            )
            if hit_tp1:
                if self.direction == "buy":
                    new_sl = self.entry + self.sl_buffer
                else:
                    new_sl = self.entry - self.sl_buffer
                self.sl = round(new_sl, self.precision)
                self.stop_loss = self.sl
                self._reached.add(0)
                return self.sl

                # Handle TP2 move
        if len(self.tp_levels) > 1 and 1 not in self._reached:
            hit_tp2 = (
                current_price >= self.tp_levels[1]
                if self.direction == "buy"
                else current_price <= self.tp_levels[1]
            )
            if hit_tp2:
                self.sl = round(self.tp_levels[0], self.precision)
                self.stop_loss = self.sl
                self._reached.add(1)
                return self.sl
        return self.sl