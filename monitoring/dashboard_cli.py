"""Command line monitoring dashboard.

Displays current open trades, strategy scores, daily guard state and the
last few lines of the trade log. Use ``--watch`` to refresh automatically.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live

TRADE_HISTORY = "logs/trade_history.json"
SCORE_PATH = "ai_engine/strategy_scores.json"
DAILY_GUARD_PATH = "logs/daily_guard.json"
TRADE_LOG_PATH = "logs/trade_log.txt"
HEATMAP_PATH = "logs/strategy_heatmap.json"

console = Console()


def _load_json(path: str) -> Any:
    if not os.path.exists(path):
        return [] if path.endswith(".json") else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return [] if path.endswith(".json") else {}


def _tail_log(path: str, lines: int = 5) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        content = f.readlines()
    return [line.rstrip() for line in content[-lines:]]

def _load_heatmap() -> Dict[str, Dict[str, Dict[str, Any]]]:
    data = _load_json(HEATMAP_PATH)
    return data if isinstance(data, dict) else {}


def _color_pnl(value: float | None) -> str:
    if value is None:
        return "[yellow]-[/]"
    if value > 0:
        color = "green"
    elif value < 0:
        color = "red"
    else:
        color = "yellow"
    return f"[{color}]{value:+.2f}%[/]"


def build_dashboard() -> Panel:
    open_trades = [t for t in _load_json(TRADE_HISTORY) if str(t.get("result")) == "open"]
    scores: Dict[str, Dict[str, Any]] = _load_json(SCORE_PATH)
    guard: Dict[str, Any] = _load_json(DAILY_GUARD_PATH)
    log_lines = _tail_log(TRADE_LOG_PATH)
    heatmap = _load_heatmap()

    trade_table = Table(title="Open Trades", expand=True)
    trade_table.add_column("Symbol")
    trade_table.add_column("TF")
    trade_table.add_column("Strategy")
    trade_table.add_column("Entry", justify="right")
    trade_table.add_column("PnL%", justify="right")

    for t in open_trades:
        pnl = t.get("profit_pct")
        trade_table.add_row(
            str(t.get("symbol")),
            str(t.get("timeframe")),
            str(t.get("strategy")),
            f"{t.get('entry', 0):.2f}",
            _color_pnl(pnl),
        )

    score_table = Table(title="Strategy Scores", expand=True)
    score_table.add_column("Strategy")
    score_table.add_column("Regime")
    score_table.add_column("Win%", justify="right")
    score_table.add_column("Recent", justify="right")
    score_table.add_column("Fit", justify="right")

    for strat, regimes in scores.items():
        if not isinstance(regimes, dict):
            continue
        for reg, m in regimes.items():
            score_table.add_row(
                strat,
                reg,
                f"{float(m.get('win_rate', 0.0)):.1f}",
                f"{float(m.get('recent_score', 0.0)):.2f}",
                f"{float(m.get('regime_fit', 0.0)):.2f}",
            )

    guard_table = Table(title="Daily Guard", expand=True)
    for k, v in guard.items():
        guard_table.add_row(str(k), str(v))

    heat_table = Table(title="Strategy Heatmap", expand=True)
    heat_table.add_column("Context")
    heat_table.add_column("Strategy")
    heat_table.add_column("Wins", justify="right")
    heat_table.add_column("Losses", justify="right")
    for context, strat_map in heatmap.items():
        for strat, stats in strat_map.items():
            heat_table.add_row(
                context,
                strat,
                str(stats.get("wins", 0)),
                str(stats.get("losses", 0)),
            )

    log_table = Table(title="Recent Log", expand=True)
    for line in log_lines:
        log_table.add_row(line)

    container_table = Table.grid(expand=True)
    container_table.add_row(trade_table)
    container_table.add_row(score_table)
    container_table.add_row(guard_table)
    container_table.add_row(heat_table)
    container_table.add_row(log_table)
    return Panel(container_table, title="AutoTrade Dashboard")


def run_dashboard(watch: int | None = None) -> None:
    if watch:
        with Live(build_dashboard(), console=console, refresh_per_second=1):
            while True:
                time.sleep(watch)
                console.clear()
                console.print(build_dashboard())
    else:
        console.print(build_dashboard())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AutoTrade Monitoring Dashboard")
    parser.add_argument("--watch", type=int, default=None, help="Refresh interval in seconds")
    args = parser.parse_args()
    run_dashboard(args.watch)