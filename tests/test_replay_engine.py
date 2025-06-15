import json
from ai_engine.trade_replayer import ReplayEngine
from ai_engine.score_updater import load_scores


def test_replay_updates_scores(tmp_path):
    history = [
        {
            "strategy": "StratA",
            "result": "TP1 hit",
            "regime": "bull",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        {
            "strategy": "StratA",
            "result": "SL hit",
            "regime": "bull",
            "timestamp": "2024-01-02T00:00:00Z"
        },
    ]
    hist_file = tmp_path / "hist.json"
    score_file = tmp_path / "scores.json"
    hist_file.write_text(json.dumps(history))
    score_file.write_text(json.dumps({}))

    engine = ReplayEngine(history_path=str(hist_file), score_path=str(score_file))
    summary = engine.run(dry_run=False)

    scores = load_scores(str(score_file))
    assert "StratA" in scores
    assert summary["StratA"]["processed"] == 2