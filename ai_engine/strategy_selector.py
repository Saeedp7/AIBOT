"""Strategy signal selector based on historical performance.

This module exposes `get_best_signal` which takes live strategy signals and
historical score metrics to return a consolidated trading signal.
"""

from __future__ import annotations

from typing import Dict, Optional
import random

# Default location for the strategy score memory
DEFAULT_SCORE_PATH = "ai_engine/strategy_scores.json"
# Minimum average composite score required to act on a direction
DEFAULT_THRESHOLD = 0.9
# Minimum confidence for any decision
MIN_CONFIDENCE = 0.1
# If scores differ by less than this, treat them as equal
EPSILON = 0.05

def load_scores(path: str = DEFAULT_SCORE_PATH) -> Dict[str, dict]:
    """Return mapping of strategy names to unified score metrics."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        raw = {}
    aggregated: Dict[str, dict] = {}
    for strat, meta in raw.items():
        if isinstance(meta, dict) and meta:
            first_val = next(iter(meta.values()))
            if isinstance(first_val, dict) and "win_rate" in first_val:
                wins = recents = fits = 0.0
                count = 0
                for m in meta.values():
                    wins += float(m.get("win_rate", 0.0))
                    recents += float(m.get("recent_score", 0.0))
                    fits += float(m.get("regime_fit", 0.0))
                    count += 1
                if count:
                    aggregated[strat] = {
                        "win_rate": wins / count,
                        "recent_score": recents / count,
                        "regime_fit": fits / count,
                    }
                continue

            aggregated[strat] = {
                "win_rate": float(meta.get("win_rate", 0.0)),
                "recent_score": float(meta.get("recent_score", 0.0)),
                "regime_fit": float(meta.get("regime_fit", 1.0)),
            }
        else:
            aggregated[strat] = {
                "win_rate": 0.0,
                "recent_score": 0.0,
                "regime_fit": 1.0,
            }
    return aggregated



# We import json after defining load_scores to keep imports grouped at top
import json


def _composite_score(metrics: dict) -> float:
    """Return composite score from metrics dictionary."""
    win_rate = float(metrics.get("win_rate", 0.0))
    recent_score = float(metrics.get("recent_score", 0.0))
    regime_fit = float(metrics.get("regime_fit", 0.0))
    return (win_rate / 100.0) * recent_score * regime_fit


def get_best_signal(
    signals: Dict[str, Optional[str]],
    scores: Dict[str, dict],
    threshold: float = DEFAULT_THRESHOLD,
) -> Optional[str]:
    """Return 'buy', 'sell' or None based on composite score comparison."""

    buy_scores: list[float] = []
    sell_scores: list[float] = []

    for strat_name, signal in signals.items():
        if signal not in ("buy", "sell"):
            continue
        metrics = scores.get(strat_name, {})
        composite = _composite_score(metrics)
        if signal == "buy":
            buy_scores.append(composite)
        else:
            sell_scores.append(composite)

    avg_buy = sum(buy_scores) / len(buy_scores) if buy_scores else 0.0
    avg_sell = sum(sell_scores) / len(sell_scores) if sell_scores else 0.0

    if avg_buy < MIN_CONFIDENCE and avg_sell < MIN_CONFIDENCE:
        return None

    if abs(avg_buy - avg_sell) < EPSILON and max(avg_buy, avg_sell) > MIN_CONFIDENCE:
        return random.choice(["buy", "sell"])

    if avg_buy > avg_sell and avg_buy > threshold:
        return "buy"
    if avg_sell > avg_buy and avg_sell > threshold:
        return "sell"
    return None
