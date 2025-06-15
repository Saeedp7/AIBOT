from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Tuple

try:
    from rich import print
except Exception:  # pragma: no cover - fallback
    pass

from config.manager import get_config
from connectors.mt5_connector import initialize_mt5, shutdown_mt5, get_account_info
from execution.spread_guard import MAX_SPREAD
from risk_management.session_guard import _BLOCKED
from risk_management.daily_guard import DailyGuard

SCORE_PATH = "ai_engine/strategy_scores.json"
TRADE_LOG = "logs/trade_log.txt"
HISTORY_FILE = "logs/trade_history.json"
DAILY_GUARD_FILE = "logs/daily_guard.json"


def check_mt5(debug: bool = False) -> Tuple[bool, str]:
    try:
        if not initialize_mt5():
            return False, "initialization failed"
        info = get_account_info()
        if debug:
            print(f"[yellow]Account info:[/] {info}")
        return True, "connection verified"
    except Exception as exc:
        return False, str(exc)
    finally:
        try:
            shutdown_mt5()
        except Exception:
            pass


def check_strategy_scores() -> Tuple[bool, str]:
    if not os.path.exists(SCORE_PATH):
        return False, "file missing"
    try:
        with open(SCORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return True, f"loaded ({len(data)} strategies)"
        return False, "invalid structure"
    except Exception as exc:
        return False, str(exc)


def check_trade_log() -> Tuple[bool, str]:
    try:
        os.makedirs(os.path.dirname(TRADE_LOG), exist_ok=True)
        with open(TRADE_LOG, "a", encoding="utf-8") as f:
            f.write("")
        return True, "writable"
    except Exception as exc:
        return False, str(exc)


def check_live_mode() -> Tuple[bool, str]:
    live = get_config("LIVE_MODE", "false").lower() == "true"
    return live, "TRUE" if live else "FALSE"


def check_guards() -> Tuple[bool, str]:
    ok = MAX_SPREAD > 0 and bool(_BLOCKED)
    return ok, "configured" if ok else "misconfigured"


def check_daily_guard() -> Tuple[bool, str]:
    if not os.path.exists(DAILY_GUARD_FILE):
        return False, "missing"
    try:
        with open(DAILY_GUARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        trades = data.get("trades", 0)
        pnl = data.get("pnl", 0.0)
        return True, f"{trades} trades today, PnL: {pnl:+.1f}%"
    except Exception as exc:
        return False, str(exc)


def check_dashboard() -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            [sys.executable, "monitoring/dashboard_cli.py"],
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, "responsive"
        return False, f"exit {result.returncode}"
    except Exception as exc:
        return False, str(exc)


def check_trade_history() -> Tuple[bool, str]:
    if not os.path.exists(HISTORY_FILE):
        return False, "missing"
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = len(data) if isinstance(data, list) else 0
        return (entries > 0, f"{entries} entries")
    except Exception as exc:
        return False, str(exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="System readiness checker")
    parser.add_argument("--report", action="store_true", help="Print readiness report")
    parser.add_argument("--debug", action="store_true", help="Verbose output")
    args = parser.parse_args()

    checks = [
        ("MT5 connection", lambda: check_mt5(args.debug)),
        ("strategy_scores.json", check_strategy_scores),
        ("trade_log.txt", check_trade_log),
        ("LIVE_MODE", check_live_mode),
        ("spread/session guards", check_guards),
        ("Daily Guard", check_daily_guard),
        ("dashboard_cli.py", check_dashboard),
        ("trade_history.json", check_trade_history),
    ]

    all_ok = True
    for label, func in checks:
        ok, info = func()
        prefix = "✅" if ok else "❌"
        print(f"{prefix} {label} {info}")
        if not ok:
            all_ok = False
    if args.report:
        print()
        if all_ok:
            print("📈 All Systems GO. Ready for LIVE MODE.")
        else:
            print("⚠️  Issues detected. Review above before going live.")


if __name__ == "__main__":
    main()