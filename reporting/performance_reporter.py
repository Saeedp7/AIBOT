from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List

HISTORY_PATH = os.path.join("logs", "trade_history.json")
REPORT_PATH = os.path.join("logs", "performance_report.json")


def load_history(path: str = HISTORY_PATH) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def compute_summary(history: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Dict[str, float]]]]:
    summary: Dict[str, Dict[str, Dict[str, Dict[str, float]]]] = {}
    for trade in history:
        if not trade or str(trade.get("result", "")).lower() in ("", "open"):
            continue
        strat = str(trade.get("strategy", ""))
        symbol = str(trade.get("symbol", ""))
        tf = str(trade.get("timeframe", ""))
        rec = summary.setdefault(strat, {}).setdefault(symbol, {}).setdefault(
            tf,
            {"trades": 0, "wins": 0, "pnl_total": 0.0, "duration_total": 0.0},
        )
        rec["trades"] += 1
        result = str(trade.get("result", "")).lower()
        if result.startswith("tp") or result == "win":
            rec["wins"] += 1
        rec["pnl_total"] += float(trade.get("profit_pct", 0.0))
        rec["duration_total"] += float(trade.get("duration", 0.0))

    for strat_map in summary.values():
        for sym_map in strat_map.values():
            for stats in sym_map.values():
                trades = stats["trades"]
                stats["win_rate"] = (stats["wins"] / trades * 100) if trades else 0.0
                stats["avg_pnl"] = stats["pnl_total"] / trades if trades else 0.0
                stats["avg_duration"] = (
                    stats["duration_total"] / trades if trades else 0.0
                )
                stats.pop("wins", None)
                stats.pop("pnl_total", None)
                stats.pop("duration_total", None)
    return summary


def save_report(report: Dict[str, Any], path: str = REPORT_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate performance summary")
    parser.add_argument("--refresh", action="store_true", help="Recompute report")
    args = parser.parse_args()

    if args.refresh or not os.path.exists(REPORT_PATH):
        history = load_history()
        report = compute_summary(history)
        save_report(report)
    else:
        try:
            with open(REPORT_PATH, "r", encoding="utf-8") as f:
                report = json.load(f)
        except Exception:
            report = {}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()