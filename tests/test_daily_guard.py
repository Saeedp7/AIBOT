import os
import json
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from risk_management.daily_guard import DailyGuard


def test_limits_by_pnl(tmp_path):
    path = tmp_path / "guard.json"
    g = DailyGuard(loss_limit_percent=1.0, max_trades=5, data_file=str(path), starting_balance=100.0)
    g.record_trade(-0.5)
    assert g.can_trade()
    g.record_trade(-0.6)
    assert not g.can_trade()


def test_limits_by_count(tmp_path):
    path = tmp_path / "guard2.json"
    g = DailyGuard(loss_limit_percent=10.0, max_trades=2, data_file=str(path), starting_balance=100.0)
    g.record_trade(0)
    g.record_trade(0)
    assert g.hit_limits()


def test_reset_new_day(tmp_path):
    path = tmp_path / "guard3.json"
    g = DailyGuard(loss_limit_percent=1.0, max_trades=1, data_file=str(path), starting_balance=100.0)
    g.record_trade(-2.0)
    assert g.hit_limits()
    # simulate next day
    with open(path, "r") as f:
        data = json.load(f)
    data["date"] = "2000-01-01"
    with open(path, "w") as f:
        json.dump(data, f)
    g2 = DailyGuard(loss_limit_percent=1.0, max_trades=1, data_file=str(path), starting_balance=100.0)
    assert g2.trades == 0 and g2.pnl == 0.0
    assert g2.can_trade()