import json
import os
from datetime import datetime
from typing import Dict

from config.scoring_config import (
    MIN_REQUIRED_TRADES,
    WARMUP_SCORE,
    LOW_TRADE_ALPHA,
    DEFAULT_ALPHA,
    RECOVERY_DAYS,
    RECOVERY_BUMP,
    MIN_BASE_SCORE,
)

SCORES_FILE = "ai_engine/strategy_scores.json"


def load_strategy_scores(path: str = SCORES_FILE) -> Dict[str, dict]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_strategy_scores(data: Dict[str, dict], path: str = SCORES_FILE) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_strategy_score(strategy_name: str, regime: str) -> float:
    score_data = load_strategy_scores()
    stats = score_data.get(strategy_name, {}).get(regime, {})

    if stats.get("count", 0) < MIN_REQUIRED_TRADES:
        return WARMUP_SCORE

    return stats.get("score", 0.0)


def update_strategy_score(
    strategy_name: str,
    regime: str,
    result: float | None = None,
    *,
    score: float | None = None,
    symbol: str | None = None,
    result_input: float | None = None,
    score_input: float | None = None,
) -> None:
    """Update score for a strategy/regime combination.

    Parameters
    ----------
    strategy_name : str
        Name of the trading strategy.
    regime : str
        Market regime label.
    result : float | None
        Binary result value ``1`` for win, ``0`` for loss. Optional if ``score``
        is provided directly.
    score : float | None
        If provided, sets the score directly without exponential smoothing.
    symbol : str | None
        Unused placeholder for future per-symbol scoring.
    result_input, score_input : float | None
        Backwards compatibility parameters when called via ``ai.strategy_score_manager``.
    """

    # Backwards compatibility with wrapper
    if result_input is not None:
        result = result_input
    if score_input is not None:
        score = score_input
    scores = load_strategy_scores()
    strat_data = scores.setdefault(strategy_name, {}).setdefault(
        regime,
        {"score": 0.0, "count": 0, "last_updated": None},
    )

    if score is not None:
        strat_data["score"] = score
    elif result is not None:
        alpha = LOW_TRADE_ALPHA if strat_data["count"] < MIN_REQUIRED_TRADES else DEFAULT_ALPHA
        strat_data["score"] = (1 - alpha) * strat_data["score"] + alpha * result
        strat_data["count"] += 1
    strat_data["last_updated"] = datetime.utcnow().isoformat()

    save_strategy_scores(scores)


def recover_old_scores() -> None:
    scores = load_strategy_scores()
    now = datetime.utcnow()

    for strat, regimes in scores.items():
        for regime, data in regimes.items():
            last = data.get("last_updated")
            if not last:
                continue

            last_dt = datetime.fromisoformat(last)
            days_passed = (now - last_dt).days

            if days_passed >= RECOVERY_DAYS:
                score = data.get("score", 0.0)
                if score < MIN_BASE_SCORE:
                    bump = RECOVERY_BUMP * days_passed
                    data["score"] = min(MIN_BASE_SCORE, score + bump)

    save_strategy_scores(scores)