"""Utility to update strategy scores based on new results.

This module provides ``update_scores`` which applies exponential
smoothing to ``win_rate``, ``recent_score`` and ``regime_fit`` metrics
stored in ``strategy_scores.json``.
"""

from __future__ import annotations

import json
import os
from typing import Dict

DEFAULT_SCORE_PATH = "ai_engine/strategy_scores.json"


def _load_json(path: str) -> Dict[str, dict]:
    """Return JSON data from ``path`` or an empty dict on failure."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_json(data: Dict[str, dict], path: str) -> None:
    """Write ``data`` to ``path`` ensuring the directory exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def calculate_composite_score(metrics: dict) -> float:
    """Return composite score identical to ``get_best_signal`` logic."""
    win_rate = float(metrics.get("win_rate", 0.0))
    recent_score = float(metrics.get("recent_score", 0.0))
    regime_fit = float(metrics.get("regime_fit", 0.0))
    return (win_rate / 100.0) * recent_score * regime_fit


def update_scores(results: Dict[str, dict], score_path: str = DEFAULT_SCORE_PATH) -> None:
    """Update ``strategy_scores.json`` with new metrics.

    Parameters
    ----------
    results : dict
        Mapping of strategy name to metrics. Each metrics dict may
        include ``win_rate`` (percentage), ``recent_score`` and optionally
        ``regime_fit``.
    score_path : str, optional
        Path to the JSON score file. Defaults to ``DEFAULT_SCORE_PATH``.
    """
    scores = _load_json(score_path)

    for name, metrics in results.items():
        existing = scores.get(name, {"win_rate": 0.0, "recent_score": 0.0, "regime_fit": 1.0})
        existing["win_rate"] = 0.8 * float(existing.get("win_rate", 0.0)) + 0.2 * float(metrics.get("win_rate", 0.0))
        existing["recent_score"] = 0.8 * float(existing.get("recent_score", 0.0)) + 0.2 * float(metrics.get("recent_score", 0.0))
        if "regime_fit" in metrics:
            existing["regime_fit"] = 0.8 * float(existing.get("regime_fit", 1.0)) + 0.2 * float(metrics.get("regime_fit", 1.0))
        else:
            existing.setdefault("regime_fit", 1.0)
        scores[name] = existing

    _save_json(scores, score_path)

def update_strategy_score(strategy_name: str, result: str, regime: str,
                          score_path: str = DEFAULT_SCORE_PATH) -> None:
    """Convenience wrapper to update a single strategy based on a trade result.

    Parameters
    ----------
    strategy_name : str
        Name of the strategy being evaluated.
    result : str
        Outcome string such as ``"TP1 hit"`` or ``"SL hit"``.
    regime : str
        Market regime label used during the trade (``"trending"``, ``"ranging"``,
        etc.).
    score_path : str, optional
        Path to the JSON score file.
    """
    outcome_win = str(result).lower().startswith("tp") or result.lower() == "win"
    delta_metrics = {
        "win_rate": 100.0 if outcome_win else 0.0,
        "recent_score": 1.0 if outcome_win else 0.0,
        "regime_fit": 1.0 if outcome_win else 0.5,
    }
    update_scores({strategy_name: delta_metrics}, score_path)


if __name__ == "__main__":
    example = {
        "VWAPReversionStrategy": {"win_rate": 60.0, "recent_score": 0.9, "regime_fit": 1.0},
        "OrderBlockScalpingStrategy": {"win_rate": 55.0, "recent_score": 0.8}
    }
    update_scores(example)
    print("Updated strategy scores.")
    