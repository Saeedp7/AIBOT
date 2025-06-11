from __future__ import annotations

from typing import Iterable, Tuple

import pandas as pd

from strategies.base import BaseStrategy
from .market_scanner_agent import MarketScannerAgent
from .strategy_evaluator_agent import StrategyEvaluatorAgent
from .memory_evaluator_agent import MemoryEvaluatorAgent
from .regime_filter import filter_strategies
from .streak_guard import StreakGuard


class StrategySelectorAgent:
    """High level decision maker for choosing a trading direction."""

    def __init__(self, strategies: Iterable[BaseStrategy], score_path: str = "ai_engine/strategy_scores.json") -> None:
        self.strategies = list(strategies)
        self.scanner = MarketScannerAgent()
        self.evaluator = StrategyEvaluatorAgent(score_path=score_path)
        self.memory = MemoryEvaluatorAgent(score_path=score_path)
        self.guard = StreakGuard()
        self.score_path = score_path

    def select(self, symbol: str, timeframe: str) -> Tuple[str | None, str | None, str]:
        df, regime = self.scanner.scan(symbol, timeframe)
        if df is None:
            return None, None, regime
        self.memory.run()
        allowed = filter_strategies(self.strategies, regime)
        allowed = [s for s in allowed if not self.guard.is_blocked(s.__class__.__name__)]
        evaluations = self.evaluator.evaluate(allowed, df, regime)
        best = None
        best_score = -1.0
        decision = None
        for item in evaluations:
            if item["signal"] not in ("buy", "sell"):
                continue
            if item["score"] > best_score:
                best_score = item["score"]
                best = item["strategy"]
                decision = item["signal"]
        return decision, best.__class__.__name__ if best else None, regime