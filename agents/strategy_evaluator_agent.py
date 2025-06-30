from __future__ import annotations

from typing import Iterable, List, Dict

import pandas as pd

from strategies.base import BaseStrategy
from ai_engine.strategy_selector import load_scores
from ai_engine.score_updater import load_asset_scores
from config.settings import DEFAULT_CONFIDENCE_THRESHOLDS
import logging

logger = logging.getLogger(__name__)

class StrategyEvaluatorAgent:
    """Score strategies using stored metrics."""

    def __init__(
        self,
        score_path: str = "ai_engine/strategy_scores.json",
        asset_score_path: str = "ai_engine/strategy_scores_by_asset.json",
    ) -> None:
        self.score_path = score_path
        self.asset_score_path = asset_score_path

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
        asset_scores = load_asset_scores(self.asset_score_path)
        results: List[Dict] = []
        base_score = DEFAULT_CONFIDENCE_THRESHOLDS.get(regime, 0.3)
        for strat in strategies:
            name = strat.__class__.__name__
            signal = strat.check_signal(symbol, timeframe, df, regime)
            if signal == "buy" and regime in {"downtrend"}:
                logger.info(f"Skipping {name}: buy signal blocked in {regime} regime.")
                continue
            if signal == "sell" and regime in {"uptrend"}:
                logger.info(f"Skipping {name}: sell signal blocked in {regime} regime.")
                continue
            sym_score = asset_scores.get(symbol or "", {}).get(name)
            if sym_score is not None:
                confidence = float(sym_score)
            else:
                metrics = scores.get(name)
                if not metrics:
                    confidence = base_score
                else:
                    fit = float(metrics.get("regime_fit", 1.0))
                    win = float(metrics.get("win_rate", 0.0))
                    recent = float(metrics.get("recent_score", 0.0))
                    confidence = (win / 100.0) * recent * fit
                    if confidence == 0:
                        confidence = base_score
            results.append({"strategy": strat, "signal": signal, "score": confidence})
        return results