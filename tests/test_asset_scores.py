import json
from agents.strategy_evaluator_agent import StrategyEvaluatorAgent
from strategies.base import BaseStrategy

class Dummy(BaseStrategy):
    def generate_signal(self, df):
        return "buy"


def test_symbol_specific_score_override(tmp_path, monkeypatch):
    score_path = tmp_path / "scores.json"
    with open(score_path, "w") as f:
        json.dump(
            {
                "Dummy": {
                    "trending": {
                        "win_rate": 50.0,
                        "recent_score": 1.0,
                        "regime_fit": 1.0,
                    }
                }
            },
            f,
        )
    asset_path = tmp_path / "asset.json"
    with open(asset_path, "w") as f:
        json.dump({"XAUUSD": {"Dummy": 0.42}}, f)

    from ai_engine import strategy_selector as ss
    import importlib.util, importlib.machinery, os
    path = os.path.join("ai_engine", "strategy_selector.py")
    spec = importlib.util.spec_from_file_location("real_selector", path)
    real_selector = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(real_selector)

    monkeypatch.setattr(ss, "load_scores", lambda path=str(score_path): real_selector.load_scores(path))
    import agents.strategy_evaluator_agent as eva
    monkeypatch.setattr(eva, "load_scores", lambda path=str(score_path): real_selector.load_scores(path))

    agent = StrategyEvaluatorAgent(score_path=str(score_path), asset_score_path=str(asset_path))
    class DF: pass
    res = agent.evaluate([Dummy()], DF(), "trending", symbol="XAUUSD", timeframe="M1")
    assert res and abs(res[0]["score"] - 0.42) < 1e-6


def test_fallback_to_global_score(tmp_path, monkeypatch):
    score_path = tmp_path / "scores.json"
    # global metrics yield composite score of 0.5
    with open(score_path, "w") as f:
        json.dump({
            "Dummy": {"trending": {"win_rate": 50.0, "recent_score": 1.0, "regime_fit": 1.0}}
        }, f)
    asset_path = tmp_path / "asset.json"
    with open(asset_path, "w") as f:
        json.dump({}, f)

    from ai_engine import strategy_selector as ss
    import importlib.util, importlib.machinery, os
    path = os.path.join("ai_engine", "strategy_selector.py")
    spec = importlib.util.spec_from_file_location("real_selector", path)
    real_selector = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(real_selector)

    monkeypatch.setattr(ss, "load_scores", lambda path=str(score_path): real_selector.load_scores(path))
    import agents.strategy_evaluator_agent as eva
    monkeypatch.setattr(eva, "load_scores", lambda path=str(score_path): real_selector.load_scores(path))

    agent = StrategyEvaluatorAgent(score_path=str(score_path), asset_score_path=str(asset_path))
    class DF: pass
    res = agent.evaluate([Dummy()], DF(), "trending", symbol="BTCUSD", timeframe="M1")
    assert res and abs(res[0]["score"] - 0.5) < 1e-6
