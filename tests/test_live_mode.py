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

    info = types.SimpleNamespace(
        trade_mode=1,
        stops_level=0,
        point=0.01,
    )
    monkeypatch.setattr(mt5, "symbol_info", lambda symbol: info)
    
    monkeypatch.setattr(scheduler_loop, "execute_fake_order", lambda *a, **k: calls.append((a, k)) or 123)

    ticket = scheduler_loop.execute_trade("buy", "XAUUSD.", 0.1, 1.0, 2.0)

    assert isinstance(ticket, int)
    assert calls and calls[0][0][0] == "buy"
    assert not order_calls


def test_execute_trade_live_calls_mt5(monkeypatch):
    monkeypatch.setenv("LIVE_MODE", "true")
    order_calls = []
    monkeypatch.setattr(mt5, "order_send", lambda req: order_calls.append(req) or types.SimpleNamespace(order=777))
    monkeypatch.setattr(scheduler_loop, "execute_fake_order", lambda *a, **k: None)

    monkeypatch.setattr(mt5, "TRADE_ACTION_DEAL", 1, raising=False)
    monkeypatch.setattr(mt5, "ORDER_TYPE_BUY", 0, raising=False)
    monkeypatch.setattr(mt5, "ORDER_TYPE_SELL", 1, raising=False)
    monkeypatch.setattr(mt5, "ORDER_TIME_GTC", 0, raising=False)
    monkeypatch.setattr(mt5, "ORDER_FILLING_FOK", 0, raising=False)

    tick = types.SimpleNamespace(ask=1.5, bid=1.4)
    monkeypatch.setattr(mt5, "symbol_info_tick", lambda symbol: tick)
    info = types.SimpleNamespace(trade_mode=1, stops_level=0, point=0.01)
    monkeypatch.setattr(mt5, "symbol_info", lambda symbol: info)

    ticket = scheduler_loop.execute_trade("buy", "XAUUSD.", 0.1, 1.0, 2.0)

    assert order_calls and order_calls[0]["symbol"] == "XAUUSD."
    assert ticket == 777
