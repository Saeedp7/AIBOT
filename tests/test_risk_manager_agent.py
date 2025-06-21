import types

import MetaTrader5 as mt5
from agents.risk_manager_agent import RiskManagerAgent


def test_margin_check_blocks(monkeypatch):
    monkeypatch.setattr(mt5, "account_info", lambda: types.SimpleNamespace(margin_free=0))
    monkeypatch.setattr(mt5, "positions_get", lambda symbol=None: [])
    agent = RiskManagerAgent()
    ok, reason = agent.validate_trade("XAUUSD.", 1.0)
    assert not ok
    assert "margin" in reason.lower()


def test_duplicate_position(monkeypatch):
    monkeypatch.setattr(mt5, "account_info", lambda: types.SimpleNamespace(margin_free=100000))
    monkeypatch.setattr(mt5, "positions_get", lambda symbol=None: [1])
    agent = RiskManagerAgent()
    ok, reason = agent.validate_trade("XAUUSD.", 0.1)
    assert not ok
    assert "already" in reason.lower()