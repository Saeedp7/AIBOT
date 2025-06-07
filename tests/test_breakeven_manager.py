from risk_management.breakeven_manager import BreakEvenManager


def test_buy_side_updates():
    m = BreakEvenManager(entry_price=100.0, direction="buy",
                         stop_loss=99.0, tp_levels=[101.0, 102.0])
    # price below TP1 -> no change
    assert m.update_stop_loss(100.5) == 99.0
    # hit TP1 -> SL moves to entry
    assert m.update_stop_loss(101.0) == 100.0
    # hit TP2 -> SL moves to TP1
    assert m.update_stop_loss(102.0) == 101.0


def test_sell_side_updates():
    m = BreakEvenManager(entry_price=200.0, direction="sell",
                         stop_loss=201.0, tp_levels=[199.0, 198.0])
    # hit TP1 -> SL moves to entry
    assert m.update_stop_loss(199.0) == 200.0
    # hit TP2 -> SL moves to TP1
    assert m.update_stop_loss(198.0) == 199.0