"""Historical trade replay and reinforcement engine."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from ai_engine.score_updater import load_scores, update_strategy_score

HISTORY_PATH = "logs/trade_history.json"
SCORE_PATH = "ai_engine/strategy_scores.json"


class ReplayEngine:
    """Replay trades and update strategy scores."""

    def __init__(self, history_path: str = HISTORY_PATH, score_path: str = SCORE_PATH) -> None:
        self.history_path = history_path
        self.score_path = score_path
        self.summary: Dict[str, Dict[str, int | float]] = {}

    # -----------------------------------------------------
    def _load_trades(self) -> List[dict]:
        if not os.path.exists(self.history_path):
            return []
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    # -----------------------------------------------------
    @staticmethod
    def _parse_date(val: str | None) -> Optional[datetime]:
        if not val:
            return None
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None

    # -----------------------------------------------------
    def _filter(self, trades: Iterable[dict], start: Optional[datetime], end: Optional[datetime], strategy: str | None) -> Iterable[dict]:
        for t in trades:
            ts = t.get("timestamp") or t.get("close_time")
            when = self._parse_date(ts)
            if start and (when is None or when < start):
                continue
            if end and (when is None or when > end):
                continue
            if strategy and t.get("strategy") != strategy:
                continue
            yield t

    # -----------------------------------------------------
    def run(self, *, start: str | None = None, end: str | None = None, strategy: str | None = None, dry_run: bool = False) -> Dict[str, Dict[str, int | float]]:
        trades = self._load_trades()
        start_dt = self._parse_date(start)
        end_dt = self._parse_date(end)
        filtered = list(self._filter(trades, start_dt, end_dt, strategy))

        before = load_scores(self.score_path)
        counts: Dict[str, Dict[str, int]] = {}
        for t in filtered:
            result = str(t.get("result", "")).lower()
            if result in ("open", ""):
                continue
            strat = str(t.get("strategy"))
            regime = str(t.get("regime", ""))
            outcome = "win" if result.startswith("tp") or result == "win" else "loss"
            net_pct = float(t.get("net_profit_pct", 0.0))
            if not dry_run:
                update_strategy_score(
                    strat,
                    outcome,
                    net_pct,
                    regime=regime,
                    symbol=str(t.get("symbol", "")),
                    score_path=self.score_path,
                )
            c = counts.setdefault(strat, {"wins": 0, "losses": 0, "processed": 0})
            c["processed"] += 1
            if outcome == "win":
                c["wins"] += 1
            else:
                c["losses"] += 1

        after = load_scores(self.score_path)
        for strat, c in counts.items():
            before_score = before.get(strat, {})
            after_score = after.get(strat, {})
            self.summary[strat] = {
                "processed": c["processed"],
                "wins": c["wins"],
                "losses": c["losses"],
                "score_before": float(before_score.get("recent_score", 0.0)) if isinstance(before_score, dict) else 0.0,
                "score_after": float(after_score.get("recent_score", 0.0)) if isinstance(after_score, dict) else 0.0,
            }
        return self.summary


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay historical trades")
    parser.add_argument("--start-date", dest="start", help="Start date ISO 8601", default=None)
    parser.add_argument("--end-date", dest="end", help="End date ISO 8601", default=None)
    parser.add_argument("--strategy", help="Filter by strategy", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Run without saving scores")
    args = parser.parse_args()

    engine = ReplayEngine()
    summary = engine.run(start=args.start, end=args.end, strategy=args.strategy, dry_run=args.dry_run)
    if summary:
        print(json.dumps(summary, indent=2))
    else:
        print("No trades processed")