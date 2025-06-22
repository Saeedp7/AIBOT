from risk_management.breakeven_manager import BreakEvenManager
import risk_management.breakeven_manager as bem
from types import SimpleNamespace

def test_buy_side_buffer(monkeypatch):
    monkeypatch.setattr(bem, "estimate_commission", lambda s, l: 2.0)
    monkeypatch.setattr(
        bem, "get_symbol_specs", lambda s: SimpleNamespace(tick_value=1.0, tick_size=0.01)
    )
    m = BreakEvenManager(
        entry_price=100.0,
        direction="buy",
        stop_loss=99.0,
        tp_levels=[101.0],
        symbol="XAUUSD",
        lot=1.0,
        precision=2,
    )
    # price below TP1 -> no change
    assert m.update_stop_loss(100.5) == 99.0
    # hit TP1 -> SL moves to breakeven plus commission buffer
    assert m.update_stop_loss(101.0) == 100.02


def test_sell_side_buffer(monkeypatch):
    monkeypatch.setattr(bem, "estimate_commission", lambda s, l: 2.0)
    monkeypatch.setattr(
        bem, "get_symbol_specs", lambda s: SimpleNamespace(tick_value=1.0, tick_size=0.01)
    )
    m = BreakEvenManager(
        entry_price=200.0,
        direction="sell",
        stop_loss=201.0,
        tp_levels=[199.0],
        symbol="XAUUSD",
        lot=1.0,
        precision=2,
    )
    # hit TP1 -> SL moves to breakeven minus buffer
    assert m.update_stop_loss(199.0) == 199.98