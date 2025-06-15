from datetime import datetime, timezone
import types

from risk_management.session_guard import session_allowed
from risk_management import session_guard


def test_session_allowed_market_open(monkeypatch):
    monkeypatch.setattr(session_guard, "symbol_info_tick", lambda s: types.SimpleNamespace(trade_mode=1))
    now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert session_allowed("XAUUSD", now)


def test_session_blocked_when_closed(monkeypatch):
    monkeypatch.setattr(session_guard, "symbol_info_tick", lambda s: types.SimpleNamespace(trade_mode=0))
    now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert not session_allowed("XAUUSD", now)


def test_session_fallback_on_missing_data(monkeypatch):
    monkeypatch.setattr(session_guard, "symbol_info_tick", lambda s: None)
    now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    assert session_allowed("XAUUSD", now)