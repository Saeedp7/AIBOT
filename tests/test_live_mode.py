import types

import MetaTrader5 as mt5
from live import scheduler_loop


def test_execute_trade_uses_mock(monkeypatch):
    calls = []

    # Ensure LIVE_MODE is false
    monkeypatch.setenv("LIVE_MODE", "false")

    # Dummy tick data
    tick = types.SimpleNamespace(ask=1.2, bid=1.1)
    monkeypatch.setattr(mt5, "symbol_info_tick", lambda symbol: tick)

    # Track if real order_send called
    order_calls = []
    monkeypatch.setattr(mt5, "order_send", lambda req: order_calls.append(req))

    monkeypatch.setattr(scheduler_loop, "execute_fake_order", lambda *a, **k: calls.append((a, k)) or 123)

    ticket = scheduler_loop.execute_trade("buy", "XAUUSD.", 0.1, 1.0, 2.0)

    assert isinstance(ticket, int)
    assert calls and calls[0][0][0] == "buy"
    assert not order_calls