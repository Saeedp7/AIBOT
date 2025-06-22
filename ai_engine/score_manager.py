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
MIN_SCORE = 0.5  # Prevent scores from decaying to useless values
DECAY_RATE = 0.94  # smoothing factor for score updates

# Scoring weights for trade outcomes
_OUTCOME_WEIGHTS = {
    "tp1": 1.0,
    "tp2": 1.5,
    "tp3": 2.0,
    "sl": -2.0,
    "closedearly": -1.0,
}


def _upgrade_legacy_scores(scores: Dict[str, dict]) -> Dict[str, dict]:
    """Return ``scores`` with legacy single-level metrics converted."""
    for strat, data in list(scores.items()):
        if isinstance(data, dict) and any(k in data for k in ("win_rate", "recent_score", "regime_fit")):
            if not any(isinstance(v, dict) for v in data.values()):
                metrics = {
                    "win_rate": float(data.get("win_rate", 0.0)),
                    "recent_score": float(data.get("recent_score", 1.0)),
                    "regime_fit": float(data.get("regime_fit", 1.0)),
                }
                scores[strat] = {"unknown": metrics}
    return scores


def _load_json(path: str) -> List[dict] | Dict[str, dict]:
    if not os.path.exists(path):
        return [] if path.endswith("json") and "history" in path else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            return loaded if isinstance(loaded, (dict, list)) else {}
    except (json.JSONDecodeError, OSError):
        return {} if "score" in path else []


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
    alpha: float = 1 - DECAY_RATE,
) -> None:
    """Update strategy metrics using ``trade_history.json``."""
    history: List[dict] = _load_json(history_path)  # type: ignore
    scores: Dict[str, dict] = _upgrade_legacy_scores(_load_json(score_path))  # type: ignore

    temp: Dict[Tuple[str, str], List[float]] = {}
    recent: Dict[Tuple[str, str], float] = {}

    for trade in history:
        if not trade or trade.get("result") in (None, "open"):
            continue
        strat = trade.get("strategy") or ""
        regime = trade.get("regime") or "unknown"
        result = str(trade.get("result", "")).lower()
        raw_pct = trade.get("net_profit_pct", trade.get("profit_pct", 0.0))
        net_pct = float(raw_pct) if raw_pct is not None else 0.0
        if net_pct < 0:
            result = "loss"
        value = _score_from_result(result, trade.get("closed_early", False))
        key = (strat, regime)
        temp.setdefault(key, []).append(value)
        prev = recent.get(key, 1.0)
        recent[key] = alpha * value + (1 - alpha) * prev

    for (strat, regime), results in temp.items():
        metrics = scores.setdefault(strat, {}).get(
            regime,
            {"win_rate": 0.0, "recent_score": 1.0, "regime_fit": 1.0},
        )

        wins = sum(1 for r in results[-10:] if r > 0)
        count = min(len(results[-10:]), 10)
        win_rate = (wins / count * 100) if count else 0.0

        recent_score = recent[(strat, regime)]

        metrics["win_rate"] = win_rate
        metrics["recent_score"] = max(recent_score, MIN_SCORE)
        metrics["regime_fit"] = max(recent_score, MIN_SCORE)
        scores.setdefault(strat, {})[regime] = metrics

    # Apply decay with lower bound
    for strat, regimes in scores.items():
        if not isinstance(regimes, dict):
            continue
        for reg, metrics in regimes.items():
            if (strat, reg) not in recent:
                metrics["recent_score"] = max((1 - alpha) * float(metrics.get("recent_score", 1.0)), MIN_SCORE)
                metrics["regime_fit"] = max((1 - alpha) * float(metrics.get("regime_fit", 1.0)), MIN_SCORE)
                regimes[reg] = metrics

    _save_json(scores, score_path)
