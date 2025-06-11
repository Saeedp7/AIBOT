from __future__ import annotations

from typing import Set

from utils.trade_journal import HISTORY_PATH
from ai_engine.score_manager import update_scores_from_trade_history


class MemoryEvaluatorAgent:
    """Update strategy scores from trade history with decay."""

    def __init__(self, score_path: str = "ai_engine/strategy_scores.json") -> None:
        self.score_path = score_path
        self.processed: Set[int] = set()

    def run(self) -> None:
        update_scores_from_trade_history(history_path=HISTORY_PATH, score_path=self.score_path)