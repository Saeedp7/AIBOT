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


def update_strategy_score(strategy_name: str, regime: str, result: float) -> None:
    scores = load_strategy_scores()
    strat_data = scores.setdefault(strategy_name, {}).setdefault(
        regime,
        {"score": 0.0, "count": 0, "last_updated": None},
    )

    previous = strat_data["score"]
    count = strat_data["count"]

    alpha = LOW_TRADE_ALPHA if count < MIN_REQUIRED_TRADES else DEFAULT_ALPHA
    new_score = (1 - alpha) * previous + alpha * result

    strat_data["score"] = new_score
    strat_data["count"] = count + 1
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