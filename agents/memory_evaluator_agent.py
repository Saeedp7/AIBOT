from __future__ import annotations

from typing import Set

from utils.trade_journal import HISTORY_PATH
from ai_engine.score_manager import update_scores_from_trade_history
from utils.cooldown_tracker import get_last_used_timestamp

class MemoryEvaluatorAgent:
    """Update strategy scores from trade history with decay."""

    def __init__(self, score_path: str = "ai_engine/strategy_scores.json") -> None:
        self.score_path = score_path
        self.processed: Set[int] = set()

    def run(self) -> None:
        update_scores_from_trade_history(history_path=HISTORY_PATH, score_path=self.score_path)

    def get_last_used_timestamp(self, strategy, symbol: str, timeframe: str):
        """Return last time ``strategy`` was used for symbol/timeframe."""
        name = strategy.__class__.__name__ if not isinstance(strategy, str) else strategy
        return get_last_used_timestamp(name, symbol, timeframe)