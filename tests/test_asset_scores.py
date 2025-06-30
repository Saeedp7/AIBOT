import json
from agents.strategy_evaluator_agent import StrategyEvaluatorAgent
from strategies.base import BaseStrategy

class Dummy(BaseStrategy):
    def generate_signal(self, df):
        return "buy"


def test_symbol_specific_score_override(tmp_path):
    score_path = tmp_path / "scores.json"
    with open(score_path, "w") as f:
        json.dump({
            "Dummy": {"trending": {"win_rate": 50.0, "recent_score": 1.0, "regime_fit": 1.0}}
        }, f)
    asset_path = tmp_path / "asset.json"
    with open(asset_path, "w") as f:
        json.dump({"XAUUSD": {"Dummy": 0.42}}, f)

    agent = StrategyEvaluatorAgent(score_path=str(score_path), asset_score_path=str(asset_path))
    class DF: pass
    res = agent.evaluate([Dummy()], DF(), "trending", symbol="XAUUSD", timeframe="M1")
    assert res and abs(res[0]["score"] - 0.42) < 1e-6
