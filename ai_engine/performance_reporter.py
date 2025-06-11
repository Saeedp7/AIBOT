"""Generate performance metrics from ``logs/trade_history.json``.

The script computes per-strategy totals, win rate, average PnL and
average regime score. Results can be exported as JSON or CSV in the
``logs`` directory.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List

HISTORY_FILE = os.path.join("logs", "trade_history.json")


def load_history(path: str = HISTORY_FILE) -> List[Dict[str, Any]]:
    """Return list of trade records from ``path`` or empty list."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def compute_statistics(history: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Compute per-strategy metrics from trade ``history``."""
    stats: Dict[str, Dict[str, float]] = {}
    for trade in history:
        strat = trade.get("strategy")
        if not strat:
            continue
        rec = stats.setdefault(
            strat,
            {
                "trades": 0,
                "wins": 0,
                "pnl_total": 0.0,
                "regime_total": 0.0,
            },
        )
        rec["trades"] += 1
        result = str(trade.get("result", "")).lower()
        if result.startswith("tp") or result == "win":
            rec["wins"] += 1
        rec["pnl_total"] += float(trade.get("pnl", 0.0))
        rec["regime_total"] += float(trade.get("regime_score", 0.0))

    for rec in stats.values():
        trades = rec["trades"]
        rec["win_rate"] = (rec["wins"] / trades * 100) if trades else 0.0
        rec["avg_pnl"] = rec["pnl_total"] / trades if trades else 0.0
        rec["avg_regime_score"] = rec["regime_total"] / trades if trades else 0.0
    return stats


def save_as_json(stats: Dict[str, Dict[str, float]], path: str) -> None:
    """Write ``stats`` to ``path`` in JSON format."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


def save_as_csv(stats: Dict[str, Dict[str, float]], path: str) -> None:
    """Write ``stats`` to ``path`` as CSV."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["strategy", "trades", "win_rate", "avg_pnl", "avg_regime_score"])
        for strat, rec in stats.items():
            writer.writerow([
                strat,
                rec.get("trades", 0),
                f"{rec.get('win_rate', 0.0):.2f}",
                f"{rec.get('avg_pnl', 0.0):.2f}",
                f"{rec.get('avg_regime_score', 0.0):.2f}",
            ])


def generate_report(fmt: str = "json") -> None:
    """Load history, compute stats and save report in ``logs``."""
    history = load_history()
    stats = compute_statistics(history)
    if fmt.lower() == "csv":
        save_as_csv(stats, os.path.join("logs", "performance_report.csv"))
    else:
        save_as_json(stats, os.path.join("logs", "performance_report.json"))


if __name__ == "__main__":
    fmt = "json"
    if len(os.sys.argv) > 1:
        fmt = os.sys.argv[1]
    generate_report(fmt)