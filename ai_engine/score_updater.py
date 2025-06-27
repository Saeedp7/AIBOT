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

def update_strategy_score(
    strategy_name: str,
    result: str,
    net_profit_pct: float,
    regime: str,
    score_path: str = DEFAULT_SCORE_PATH,
    alpha: float = 0.1,
) -> None:
    """Update metrics for ``strategy_name`` after a closed trade.

    Parameters
    ----------
    strategy_name : str
        Name of the strategy being evaluated.
    result : str
        Final outcome label (``"win"`` or ``"loss"``).
    net_profit_pct : float
        Net profit or loss percentage of the trade.
    regime : str
        Market regime label used during the trade.
    score_path : str, optional
        Path to the JSON score file.
    alpha : float, optional
        Exponential smoothing factor for ``win_rate``.
    """
    if net_profit_pct is None:
        # Ensure strategy entry exists even when no result yet
        scores = _load_json(score_path)
        regime = regime or "unknown"
        scores.setdefault(strategy_name, {}).setdefault(
            regime,
            {"recent_score": 1.0, "win_rate": 50.0, "regime_fit": 1.0, "decay": 0.99},
        )
        _save_json(scores, score_path)
        return
    scores = _load_json(score_path)
    regime = regime or "unknown"
    metrics = scores.get(strategy_name, {}).get(
        regime,
        {"recent_score": 1.0, "win_rate": 50.0, "regime_fit": 1.0, "decay": 0.99},
    )

    win = str(result).lower() == "win"
    prev_recent = float(metrics.get("recent_score", 1.0))
    prev_wr = float(metrics.get("win_rate", 50.0))

    delta = (abs(net_profit_pct) / 100.0) * (1 if win else -1)
    recent_score = min(2.0, max(0.1, prev_recent + delta))
    win_rate = (1 - alpha) * prev_wr + alpha * (100.0 if win else 0.0)

    metrics["recent_score"] = recent_score
    metrics["win_rate"] = win_rate
    metrics.setdefault("regime_fit", 1.0)
    metrics.setdefault("decay", 0.99)
    scores.setdefault(strategy_name, {})[regime] = metrics
    _save_json(scores, score_path)

def load_scores(path: str = DEFAULT_SCORE_PATH) -> Dict[str, dict]:
    """Load score metrics from ``path``."""
    return _load_json(path)


def get_strategy_win_rate(strategy_name: str, path: str = DEFAULT_SCORE_PATH) -> float:
    """Return win rate percentage for ``strategy_name`` from the score file."""
    return float(load_scores(path).get(strategy_name, {}).get("win_rate", 0.0))

def update_ai_from_trade(
    *,
    ticket: int,
    result: str,
    strategy: str,
    regime: str,
    symbol: str,
    timeframe: str,
    net_profit_pct: float,
    tp_hits: list,
) -> None:
    """Analyze trade outcome and update AI memory."""
    from ai_engine.memory import strategy_memory

    outcome = str(result or "").lower()
    if outcome.startswith("tp"):
        feedback_score = 1.0
    elif outcome == "closed_early":
        feedback_score = 0.5
    elif outcome == "stopped_out":
        feedback_score = -1.0
    else:
        feedback_score = 0.0

    bonus = len(tp_hits) * 0.2
    adjusted = feedback_score + bonus

    strategy_memory.update_score(
        symbol=symbol,
        timeframe=timeframe,
        strategy=strategy,
        regime=regime,
        score_delta=adjusted,
    )



if __name__ == "__main__":
    example = {
        "VWAPReversionStrategy": {"win_rate": 60.0, "recent_score": 0.9, "regime_fit": 1.0},
        "OrderBlockScalpingStrategy": {"win_rate": 55.0, "recent_score": 0.8},
    }
    update_scores(example)
    print("Updated strategy scores.")