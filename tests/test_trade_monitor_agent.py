import types

import MetaTrader5 as mt5
from agents import trade_monitor_agent


def test_monitor_updates_score(monkeypatch):
    calls = []

    def fake_positions(ticket=None):
        if not calls:
            calls.append(True)
            return [types.SimpleNamespace(ticket=123)]
        return []

    monkeypatch.setattr(mt5, "positions_get", fake_positions)
    monkeypatch.setattr(mt5, "history_deals_get", lambda ticket=None: [types.SimpleNamespace(profit=1)], raising=False)
    monkeypatch.setattr(trade_monitor_agent, "update_strategy_score", lambda s, r: calls.append((s, r)))
    monkeypatch.setattr(trade_monitor_agent, "update_trade", lambda *a, **k: None)
    monkeypatch.setattr(trade_monitor_agent.time, "sleep", lambda s: None)

    agent = trade_monitor_agent.TradeMonitorAgent(123, "Strat", "XAUUSD.")
    agent.wait_and_score()
    assert ("Strat", "win") in calls