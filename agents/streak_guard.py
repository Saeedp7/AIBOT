from __future__ import annotations

from utils.trade_journal import load_history


class StreakGuard:
    """Block strategies after a series of consecutive losses."""

    def __init__(self, streak: int = 2) -> None:
        """Initialize guard with consecutive loss threshold."""
        self.streak = streak

    def is_blocked(self, strategy_name: str) -> bool:
        losses = 0
        history = load_history()
        for trade in reversed(history):
            if trade.get("strategy") != strategy_name:
                continue
            result = str(trade.get("result", "")).lower()
            if result.startswith("tp") or result == "win":
                break
            if result == "open":
                continue
            losses += 1
            if losses >= self.streak:
                return True
        return False