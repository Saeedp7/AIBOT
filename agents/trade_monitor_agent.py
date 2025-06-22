from __future__ import annotations

import time
from datetime import datetime

import MetaTrader5 as mt5

from ai_engine.score_updater import update_strategy_score
from utils.trade_journal import update_trade


def analyze_trade_result(ticket: int) -> tuple[str, float]:
    """Return outcome string and profit in USD from MT5 history."""
    deals = mt5.history_deals_get(ticket=ticket)
    if not deals:
        return "loss", 0.0
    profit = sum(getattr(d, "profit", 0.0) for d in deals)
    return ("win" if profit > 0 else "loss"), profit


class TradeMonitorAgent:
    """Poll MT5 until a trade closes then update score."""

    def __init__(self, ticket: int, symbol: str, timeframe: str, strategy: str, regime: str) -> None:
        self.ticket = ticket
        self.symbol = symbol
        self.timeframe = timeframe
        self.strategy = strategy
        self.regime = regime  # ✅ FIX: Added regime tracking

    def wait_and_score(self) -> None:
        """Block until the trade closes then log the result."""
        while mt5.positions_get(ticket=self.ticket):
            time.sleep(5)
        outcome, profit = analyze_trade_result(self.ticket)
        update_strategy_score(self.strategy, outcome, getattr(self, "regime", "unknown"))
        update_trade(self.ticket, close_time=datetime.utcnow().isoformat() + "Z", result=outcome, profit_pct=profit)