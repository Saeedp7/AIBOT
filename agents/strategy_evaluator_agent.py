from __future__ import annotations

from typing import Iterable, List, Dict

import pandas as pd

from strategies.base import BaseStrategy
from ai_engine.strategy_selector import load_scores
import logging

logger = logging.getLogger(__name__)

class StrategyEvaluatorAgent:
    """Score strategies using stored metrics."""

    def __init__(self, score_path: str = "ai_engine/strategy_scores.json") -> None:
        self.score_path = score_path

    def evaluate(
        self,
        strategies: Iterable[BaseStrategy],
        df: pd.DataFrame,
        regime: str,
        *,
        symbol: str | None = None,
        timeframe: str | None = None,
    ) -> List[Dict]:
        try:
            scores = load_scores(self.score_path)
        except TypeError:
            scores = load_scores()
        results: List[Dict] = []
        for strat in strategies:
            name = strat.__class__.__name__
            signal = strat.check_signal(symbol, timeframe, df, regime)
            if signal == "buy" and regime in {"downtrend"}:
                logger.info(f"Skipping {name}: buy signal blocked in {regime} regime.")
                continue
            if signal == "sell" and regime in {"uptrend"}:
                logger.info(f"Skipping {name}: sell signal blocked in {regime} regime.")
                continue
            metrics = scores.get(name, {})
            fit = float(metrics.get("regime_fit", 1.0))
            win = float(metrics.get("win_rate", 0.0))
            recent = float(metrics.get("recent_score", 0.0))
            confidence = (win / 100.0) * recent * fit
            results.append({"strategy": strat, "signal": signal, "score": confidence})
        return results