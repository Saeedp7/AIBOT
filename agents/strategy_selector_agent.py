from __future__ import annotations

from typing import Iterable, Tuple
import random

import pandas as pd

from strategies.base import BaseStrategy
import logging

logger = logging.getLogger(__name__)
from .market_scanner_agent import MarketScannerAgent
from .strategy_evaluator_agent import StrategyEvaluatorAgent
from .memory_evaluator_agent import MemoryEvaluatorAgent
from .regime_filter import filter_strategies
from .streak_guard import StreakGuard

from config.settings import EXPLORATION_PROBABILITY

MIN_CONFIDENCE = 0.1
EPSILON = 0.05

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
        evaluations = self.evaluator.evaluate(
            allowed, df, regime, symbol=symbol, timeframe=timeframe
        )
        score_map = {e["strategy"].__class__.__name__: e["score"] for e in evaluations}
        logger.info("Evaluated strategies: %s", score_map)
        scored = [
            (e["strategy"], e["signal"], e["score"])
            for e in evaluations
            if e["signal"] in ("buy", "sell")
        ]
        if not scored:
            return None, None, regime

        scored.sort(key=lambda x: x[2], reverse=True)
        top_score = scored[0][2]
        if top_score < MIN_CONFIDENCE:
            return None, None, regime

        if len(scored) > 1 and top_score - scored[1][2] < EPSILON:
            chosen = random.choice(scored[:2])
        else:
            chosen = scored[0]

        # optional exploration across viable candidates
        candidates = [s for s in scored if s[2] >= MIN_CONFIDENCE]
        if candidates and random.random() < EXPLORATION_PROBABILITY:
            chosen = random.choice(candidates)

        return chosen[1], chosen[0].__class__.__name__, regime