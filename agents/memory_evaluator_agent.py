from __future__ import annotations

from typing import Set

from utils.trade_journal import load_history
from ai_engine.score_updater import update_strategy_score


class MemoryEvaluatorAgent:
    """Update strategy scores from trade history with decay."""

    def __init__(self, score_path: str = "ai_engine/strategy_scores.json") -> None:
        self.score_path = score_path
        self.processed: Set[int] = set()

    def run(self) -> None:
        history = load_history()
        for trade in history:
            ticket = trade.get("ticket")
            if ticket in self.processed or trade.get("result") in (None, "open"):
                continue
            outcome = "win" if str(trade.get("result", "")).lower().startswith("tp") else "loss"
            update_strategy_score(trade.get("strategy", ""), outcome, regime=trade.get("regime", ""), score_path=self.score_path)
            self.processed.add(ticket)