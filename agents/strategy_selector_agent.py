"""Strategy selection combining AI memory and real-time confidence."""

from __future__ import annotations

import json
import logging
from itertools import cycle
from typing import Iterable, Tuple

import pandas as pd

from strategies.base import BaseStrategy
from .market_scanner_agent import MarketScannerAgent
from .regime_filter import filter_strategies

logger = logging.getLogger(__name__)

_REGIME_PATH = "config/strategy_regimes.json"


class StrategySelectorAgent:
    """Choose optimal strategy based on scores and live signals."""

    def __init__(self, strategies: Iterable[BaseStrategy], score_path: str = "ai_engine/strategy_scores.json", asset_score_path: str | None = None) -> None:
        self.strategies = list(strategies)
        self._cycle = cycle(self.strategies)
        self.score_path = score_path
        self.scanner = MarketScannerAgent()
        self._regime_map = self._load_regimes()

    @staticmethod
    def _load_regimes() -> dict:
        try:
            with open(_REGIME_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _valid_for_regime(self, strategy: BaseStrategy, regime: str) -> bool:
        conf = self._regime_map.get(strategy.__class__.__name__, {})
        valid = conf.get("valid_regimes")
        return not valid or regime in valid

    def select(self, symbol: str, timeframe: str) -> Tuple[str | None, str | None, str]:
        df, regime = self.scanner.scan(symbol, timeframe)
        if df is None:
            return None, None, regime
        scores_module = __import__("ai_engine.strategy_selector", fromlist=["load_scores"]);
        load_scores = scores_module.load_scores
        scores = load_scores(self.score_path)
        strategies = [s for s in self.strategies if self._valid_for_regime(s, regime)]
        if not strategies:
            return None, None, regime
        evaluations = []
        for strat in strategies:
            result = strat.generate_signal(df)
            if isinstance(result, dict):
                signal = result.get("signal")
                conf = float(result.get("confidence", 0))
            else:
                signal = result
                conf = 0.0
            metrics = scores.get(strat.__class__.__name__, {}).get(regime, {})
            ai_score = float(metrics.get("recent_score", 0))
            combined = (conf + ai_score) / 2
            evaluations.append((combined, signal, strat.__class__.__name__))
        evaluations.sort(key=lambda t: t[0], reverse=True)
        if not evaluations:
            return None, None, regime
        _, signal, name = evaluations[0]
        if signal in {"buy", "sell"}:
            return signal, name, regime
        return None, name, regime
