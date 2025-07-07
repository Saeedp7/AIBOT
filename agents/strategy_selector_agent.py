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

    def select(self, symbol: str, timeframe: str | None = None) -> Tuple[str | None, str | None, str | None, str]:
        """Evaluate all strategies using their preferred timeframes.

        Returns tuple of (signal, strategy_name, strategy_timeframe, regime).
        """
        self.memory.run()

        data_cache: dict[str, tuple[pd.DataFrame | None, str]] = {}
        evaluations = []

        for strat in self.strategies:
            tf = getattr(strat, "preferred_tf", timeframe or "M15")
            if tf not in data_cache:
                df, reg = self.scanner.scan(symbol, tf)
                data_cache[tf] = (df, reg)
            else:
                df, reg = data_cache[tf]

            if df is None:
                continue

            allowed = getattr(strat, "regimes", None)
            if hasattr(strat, "allowed_regimes"):
                allowed = strat.allowed_regimes()
            if allowed and reg not in allowed:
                continue

            result = self.evaluator.evaluate([strat], df, reg, symbol=symbol, timeframe=tf)
            if not result:
                continue
            ev = result[0]
            ev["timeframe"] = tf
            ev["regime"] = reg
            evaluations.append(ev)

        if not evaluations:
            return None, None, timeframe, "unknown"

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
            return None, None, evaluations[0].get("timeframe"), evaluations[0].get("regime", "unknown")

        strategy = evaluation["strategy"]
        score = evaluation["score"]
        signal = evaluation["signal"]
        tf = evaluation.get("timeframe")
        reg = evaluation.get("regime", "unknown")
        name = strategy.__class__.__name__

        logger.info("Evaluated %s (%s): %.2f -> %s", name, tf, score, signal)

        if signal in ("buy", "sell") and score >= MIN_CONFIDENCE:
            return signal, name, tf, reg

        debug_log(
            f"{name} {symbol} {tf} signal={signal} score={score:.2f} < {MIN_CONFIDENCE}"
        )
        return None, name, tf, reg
