"""Strategy score management from trade history.

This module computes performance metrics per strategy and market regime
by scanning ``trade_history.json``. Metrics include win rate for the last
10 closed trades, an exponentially smoothed ``recent_score`` and a
``regime_fit`` value. Results are saved to ``strategy_scores.json``.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Tuple

DEFAULT_HISTORY_PATH = "logs/trade_history.json"
DEFAULT_SCORE_PATH = "ai_engine/strategy_scores.json"

# Scoring weights for trade outcomes
_OUTCOME_WEIGHTS = {
    "tp1": 1.0,
    "tp2": 1.5,
    "tp3": 2.0,
    "sl": -2.0,
    "closedearly": -1.0,
}


def _load_json(path: str) -> List[dict] | Dict[str, dict]:
    if not os.path.exists(path):
        return [] if path.endswith(".json") else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return [] if path.endswith(".json") else {}


def _save_json(data: Dict[str, dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _score_from_result(result: str, closed_early: bool = False) -> float:
    result = str(result).lower()
    if closed_early or "closed" in result:
        return _OUTCOME_WEIGHTS["closedearly"]
    if "tp3" in result:
        return _OUTCOME_WEIGHTS["tp3"]
    if "tp2" in result:
        return _OUTCOME_WEIGHTS["tp2"]
    if "tp1" in result or result.startswith("tp"):
        return _OUTCOME_WEIGHTS["tp1"]
    if "sl" in result or "loss" in result:
        return _OUTCOME_WEIGHTS["sl"]
    return 0.0


def update_scores_from_trade_history(
    history_path: str = DEFAULT_HISTORY_PATH,
    score_path: str = DEFAULT_SCORE_PATH,
    *,
    alpha: float = 0.2,
) -> None:
    """Update strategy metrics using ``trade_history.json``.

    Parameters
    ----------
    history_path : str
        Location of the trade history JSON file.
    score_path : str
        Destination path for the updated score file.
    alpha : float, optional
        Smoothing factor for the ``recent_score``.
    """

    history: List[dict] = _load_json(history_path)  # type: ignore[assignment]
    scores: Dict[str, dict] = _load_json(score_path)  # type: ignore[assignment]

    # temporary containers
    temp: Dict[Tuple[str, str], List[float]] = {}
    recent: Dict[Tuple[str, str], float] = {}

    for trade in history:
        if not trade or trade.get("result") in (None, "open"):
            continue
        strat = trade.get("strategy") or ""
        regime = trade.get("regime") or "unknown"
        value = _score_from_result(trade.get("result"), trade.get("closed_early", False))
        key = (strat, regime)
        temp.setdefault(key, []).append(value)
        prev = recent.get(key, 0.0)
        recent[key] = alpha * value + (1 - alpha) * prev

    for (strat, regime), results in temp.items():
        metrics = scores.setdefault(strat, {}).get(
            regime,
            {"win_rate": 0.0, "recent_score": 0.0, "regime_fit": 1.0},
        )

        wins = sum(1 for r in results[-10:] if r > 0)
        count = min(len(results[-10:]), 10)
        win_rate = (wins / count * 100) if count else 0.0

        recent_score = recent[(strat, regime)]

        metrics["win_rate"] = win_rate
        metrics["recent_score"] = recent_score
        metrics["regime_fit"] = recent_score
        scores.setdefault(strat, {})[regime] = metrics

    # apply decay for regimes without new trades
    for strat, regimes in list(scores.items()):
        if not isinstance(regimes, dict):
            continue
        for reg, metrics in regimes.items():
            if (strat, reg) not in recent:
                metrics["recent_score"] = (1 - alpha) * float(metrics.get("recent_score", 0.0))
                metrics["regime_fit"] = (1 - alpha) * float(metrics.get("regime_fit", 1.0))
                regimes[reg] = metrics
        scores[strat] = regimes

    _save_json(scores, score_path)