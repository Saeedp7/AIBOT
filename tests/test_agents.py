import json
import types

from agents.strategy_selector_agent import StrategySelectorAgent
from agents.market_scanner_agent import MarketScannerAgent
from agents.streak_guard import StreakGuard
from strategies.base import BaseStrategy
from utils import trade_journal


def test_streak_guard_blocks(tmp_path, monkeypatch):
    hist = [
        {"ticket": 1, "strategy": "TestStrat", "result": "loss"},
        {"ticket": 2, "strategy": "TestStrat", "result": "loss"},
        {"ticket": 3, "strategy": "TestStrat", "result": "loss"},
    ]
    path = tmp_path / "hist.json"
    with open(path, "w") as f:
        json.dump(hist, f)
    monkeypatch.setattr(trade_journal, "HISTORY_PATH", str(path))
    guard = StreakGuard()
    assert guard.is_blocked("TestStrat")


def test_strategy_selector_agent(tmp_path, monkeypatch):
    class Dummy:
        def copy(self, deep=True):
            return self

    df = Dummy()
    score_path = tmp_path / "scores.json"
    with open(score_path, "w") as f:
        json.dump({
            "GoodStrategy": {"win_rate": 90, "recent_score": 1.0, "regime_fit": 1.0},
            "BadStrategy": {"win_rate": 10, "recent_score": 0.1, "regime_fit": 1.0},
        }, f)
    hist_path = tmp_path / "hist.json"
    with open(hist_path, "w") as f:
        json.dump([], f)
    monkeypatch.setattr(trade_journal, "HISTORY_PATH", str(hist_path))

    class GoodStrategy(BaseStrategy):
        def generate_signal(self, df):
            return "buy"

    class BadStrategy(BaseStrategy):
        def generate_signal(self, df):
            return "sell"

    def fake_scan(self, symbol, timeframe):
        return df, "trending"

    monkeypatch.setattr(MarketScannerAgent, "scan", fake_scan)

    from ai_engine import strategy_selector as ss
    monkeypatch.setattr(ss, "load_scores", lambda path=str(score_path): json.load(open(path)))

    agent = StrategySelectorAgent([GoodStrategy(), BadStrategy()], score_path=str(score_path))
    decision, strat_name, regime = agent.select("XAUUSD", "M1")
    assert decision == "buy"
    assert strat_name == "GoodStrategy"
    assert regime == "trending"