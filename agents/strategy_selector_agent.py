from __future__ import annotations

from typing import Iterable, Tuple
import random
from itertools import cycle

import pandas as pd

from strategies.base import BaseStrategy
import logging
from utils.logger import debug_log

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

    def __init__(
        self,
        strategies: Iterable[BaseStrategy],
        score_path: str = "ai_engine/strategy_scores.json",
        asset_score_path: str = "ai_engine/strategy_scores_by_asset.json",
    ) -> None:
        self.strategies = list(strategies)
        self._strategy_cycle = cycle(self.strategies)
        self.scanner = MarketScannerAgent()
        self.evaluator = StrategyEvaluatorAgent(
            score_path=score_path, asset_score_path=asset_score_path
        )
        self.memory = MemoryEvaluatorAgent(score_path=score_path)
        # Block strategies after two consecutive losses
        self.guard = StreakGuard(streak=2)
        self.score_path = score_path
        self.asset_score_path = asset_score_path

    def select(self, symbol: str, timeframe: str) -> Tuple[str | None, str | None, str]:
        df, regime = self.scanner.scan(symbol, timeframe)
        if df is None:
            return None, None, regime

        self.memory.run()

        strategies = filter_strategies(self.strategies, regime)
        if not strategies:
            return None, None, regime

        evaluations = self.evaluator.evaluate(
            strategies, df, regime, symbol=symbol, timeframe=timeframe
        )
        evaluations.sort(key=lambda e: e["score"], reverse=True)

        if random.random() < EXPLORATION_PROBABILITY:
            evaluation = random.choice(evaluations)
        else:
            evaluation = None
            for ev in evaluations:
                name = ev["strategy"].__class__.__name__
                if not self.guard.is_blocked(name):
                    evaluation = ev
                    break

        if evaluation is None:
            debug_log("All strategies blocked by streak guard")
            return None, None, regime

        strategy = evaluation["strategy"]

        score = evaluation["score"]
        signal = evaluation["signal"]
        name = strategy.__class__.__name__
        logger.info("Evaluated %s: %.2f -> %s", name, score, signal)

        if signal in ("buy", "sell") and score >= MIN_CONFIDENCE:
            return signal, name, regime

        debug_log(
            f"{name} {symbol} {timeframe} signal={signal} score={score:.2f} < {MIN_CONFIDENCE}"
        )
        return None, name, regime