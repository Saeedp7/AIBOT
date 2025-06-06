# ✅ Project Audit: AutoTrade AI Bot

import os
import importlib
import traceback
from pathlib import Path

ROOT = Path(".")


def check_imports():
    print("\n🔍 Checking module imports...")
    errors = []
    for module_path in ROOT.rglob("*.py"):
        if any(x in module_path.parts for x in ["venv", "__pycache__", "tests"]):
            continue
        rel_path = module_path.with_suffix("").relative_to(ROOT)
        module_name = ".".join(rel_path.parts)
        try:
            importlib.import_module(module_name)
        except Exception as e:
            errors.append((module_name, str(e)))
    if errors:
        for mod, err in errors:
            print(f"❌ {mod}: {err}")
    else:
        print("✅ All modules imported successfully.")


def check_strategy_interfaces():
    print("\n🧠 Validating strategy interfaces...")
    from strategies.strategy_selector import StrategySelector
    selector = StrategySelector()
    for strat in selector.strategies:
        name = strat.__class__.__name__
        if not hasattr(strat, "check_signal"):
            print(f"❌ {name} is missing check_signal(df) method")
        else:
            print(f"✅ {name} implements check_signal(df)")


def check_sl_tp_logic():
    print("\n📐 Testing SL/TP logic...")
    from risk_management.stop_loss_manager import calculate_sl_tp, determine_sl_tp
    try:
        sl, tp = calculate_sl_tp(1000, "buy", 1.5, 2.0)
        assert isinstance(tp, (float, int))
        print("✅ calculate_sl_tp returns valid tuple")
    except Exception as e:
        print(f"❌ calculate_sl_tp failed: {e}")
    try:
        import pandas as pd
        dummy = pd.DataFrame({"close": [100]*30})
        result = determine_sl_tp("VWAPReversionStrategy", 100, "buy", dummy)
        assert len(result) == 3
        print("✅ determine_sl_tp returns SL, TPs, regime")
    except Exception as e:
        print(f"❌ determine_sl_tp failed: {e}")


def check_lot_sizing():
    print("\n💰 Validating lot sizing fallback...")
    from risk_management.lot_sizing_module import calculate_lot_size
    size = calculate_lot_size(balance=10000, sl_distance=50, risk_percent=1.0, symbol="XAUUSD.")
    print(f"✅ Lot size calculated: {size}")


def check_daily_guard():
    print("\n🛡️ Checking DailyGuard behavior...")
    from risk_management.daily_guard import DailyGuard
    guard = DailyGuard(data_file="logs/daily_guard_test.json")
    guard.record_trade(-100.0)
    print(f"✅ Trades: {guard.trades} | PnL: {guard.pnl:.2f} | Can Trade: {guard.can_trade()}")
    if os.path.exists("logs/daily_guard_test.json"):
        os.remove("logs/daily_guard_test.json")


if __name__ == "__main__":
    print("\n🔎 Running AutoTrade AI Bot Full Audit...")
    check_imports()
    check_strategy_interfaces()
    check_sl_tp_logic()
    check_lot_sizing()
    check_daily_guard()
    print("\n✅ Audit Complete.")
