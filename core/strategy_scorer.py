from __future__ import annotations

import json
import os
from typing import Tuple

SCORE_FILE = "ai_engine/simple_strategy_scores.json"


def get_score_and_sample(strategy: str, regime: str) -> Tuple[float, int]:
    if not os.path.exists(SCORE_FILE):
        return 0.0, 0
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return 0.0, 0
    reg_map = data.get(strategy, {}).get(regime, {})
    return float(reg_map.get("score", 0.0)), int(reg_map.get("count", 0))


def save_score(strategy: str, score: float, regime: str, count: int) -> None:
    data = {}
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    strat_map = data.setdefault(strategy, {})
    strat_map[regime] = {"score": score, "count": count}
    data[strategy] = strat_map
    os.makedirs(os.path.dirname(SCORE_FILE), exist_ok=True)
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_score(strategy: str, result: float, regime: str) -> None:
    """Update composite score using sample-aware weighting."""
    previous_score, sample_count = get_score_and_sample(strategy, regime)
    alpha = min(0.5, 1.0 / (sample_count + 1))
    new_score = (1 - alpha) * previous_score + alpha * result
    save_score(strategy, new_score, regime, sample_count + 1)