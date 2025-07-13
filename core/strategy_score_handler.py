import json
import os
from typing import Dict

USED_SCORE_FILE = "Used_strategy_score.json"
BASE_SCORE_FILE = "Base_strategy_score.json"


def _load_json(path: str) -> Dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def load_scores(
    base_path: str = BASE_SCORE_FILE, used_path: str | None = None
) -> Dict:
    if used_path is None:
        used_path = USED_SCORE_FILE
    base_scores = _load_json(base_path)
    used_scores = _load_json(used_path)
    merged = base_scores.copy()
    for name, score in used_scores.items():
        merged[name] = score
    return merged


def get_strategy_score(name: str, *, base_path: str = BASE_SCORE_FILE, used_path: str | None = None) -> float:
    scores = load_scores(base_path=base_path, used_path=used_path)
    return float(scores.get(name, 0.0))


def update_strategy_score(name: str, *args, **kwargs) -> None:
    """Record ``name`` score in ``USED_SCORE_FILE``.

    This accepts arbitrary arguments for compatibility with older call
    signatures. ``score`` can be provided directly via keyword or the
    second positional argument.
    """

    score = kwargs.get("score")
    result = kwargs.get("result")
    if score is None and args:
        if isinstance(args[0], (int, float)):
            score = args[0]
        else:
            result = args[0]
    if score is None:
        score = 1.0 if str(result).startswith("win") or str(result).startswith("tp") else 0.0

    used_path = kwargs.get("score_path", USED_SCORE_FILE)
    used = _load_json(used_path)
    used[name] = float(score)
    with open(used_path, "w", encoding="utf-8") as f:
        json.dump(used, f, indent=2)
