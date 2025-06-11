from risk_management.exposure_guard import ExposureGuard, TIMEFRAME_WEIGHTS


def test_rejection_rules():
    guard = ExposureGuard()

    # allow first trade
    assert guard.allow("XAUUSD.", "M5", "buy", 0.8)
    guard.record("XAUUSD.", "M5", "buy", 0.8)

    # within weight limit
    assert guard.allow("XAUUSD.", "M15", "buy", 0.7)
    guard.record("XAUUSD.", "M15", "buy", 0.7)

    # weight exceeded
    assert not guard.allow("XAUUSD.", "H1", "buy", 0.9)

    # conflicting direction
    assert not guard.allow("XAUUSD.", "M1", "sell", 0.9)

    # lower-confidence duplicate
    assert not guard.allow("XAUUSD.", "M15", "buy", 0.6)