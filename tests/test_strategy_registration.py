import json
import shutil
from strategies import discover_strategies
from ai_engine.score_manager import ensure_base_scores


def test_all_strategies_have_scores(tmp_path):
    strategies = discover_strategies()
    names = [s.__class__.__name__ for s in strategies]

    score_path = tmp_path / "scores.json"
    shutil.copy("ai_engine/strategy_scores.json", score_path)

    ensure_base_scores(names, str(score_path))

    with open(score_path, "r", encoding="utf-8") as f:
        scores = json.load(f)

    missing = [n for n in names if n not in scores]
    assert not missing, f"Missing scores for: {missing}"