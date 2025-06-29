from __future__ import annotations

import time
from datetime import datetime
import logging

import MetaTrader5 as mt5

from ai_engine.score_updater import update_strategy_score
from utils.trade_journal import update_trade, load_history
from execution.multi_tp_manager import handle_order_close
from risk_management.commission_calculator import estimate_commission, estimate_swap

logger = logging.getLogger(__name__)


def analyze_trade_result(ticket: int):
    """Return outcome, profit, commission, swap, exit price and volume."""
    deals = mt5.history_deals_get(ticket=ticket)
    if not deals:
        return "loss", 0.0, 0.0, 0.0, 0.0, 0.0
    profit = sum(getattr(d, "profit", 0.0) for d in deals)
    commission = -sum(getattr(d, "commission", 0.0) for d in deals)
    swap = -sum(getattr(d, "swap", 0.0) for d in deals)
    price = getattr(deals[-1], "price", 0.0)
    volume = sum(getattr(d, "volume", 0.0) for d in deals)
    if commission == 0.0:
        symbol = getattr(deals[-1], "symbol", "")
        commission = estimate_commission(symbol, volume)
    outcome = "win" if profit > 0 else "loss"
    return outcome, profit, commission, swap, price, volume


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
        while True:
            positions = mt5.positions_get(ticket=self.ticket)
            if positions is None:
                time.sleep(5)
                continue
            if not positions:
                break
            time.sleep(5)
        (
            outcome,
            profit,
            commission,
            swap,
            exit_price,
            volume,
        ) = analyze_trade_result(self.ticket)

        history = {t["ticket"]: t for t in load_history()}
        rec = history.get(self.ticket, {})
        entry = float(rec.get("entry", 0.0))
        net_profit = profit - commission - swap
        net_pct = (
            net_profit / (entry * volume * 100000.0) * 100 if entry and volume else 0.0
        )
        gross_pct = (
            profit / (entry * volume * 100000.0) * 100 if entry and volume else 0.0
        )

        close_ts = datetime.utcnow().isoformat() + "Z"
        duration = None
        if rec.get("timestamp"):
            try:
                start = datetime.fromisoformat(rec["timestamp"].replace("Z", "+00:00"))
                duration = (datetime.utcnow() - start).total_seconds() / 60
            except Exception:
                duration = None
        result_str = outcome
        reason = "manual"
        if rec.get("closed_early"):
            result_str = rec.get("result", "closed_early")
            reason = rec.get("exit_reason", "manual")
        else:
            hit = rec.get("hit")
            if hit and hit.startswith("TP"):
                result_str = hit
                reason = "target"
            elif outcome == "loss":
                result_str = "SL hit"
                reason = "loss"
        update_trade(
            self.ticket,
            exit=exit_price,
            close_time=close_ts,
            result=result_str,
            profit_pct=gross_pct,
            net_profit_pct=net_pct,
            commission_usd=commission,
            swap_usd=swap,
            duration=duration,
            exit_reason=reason,
        )
        handle_order_close(self.ticket, exit_price)
        try:
            import inspect

            sig = inspect.signature(update_strategy_score)
            if len(sig.parameters) >= 4:
                update_strategy_score(self.strategy, result_str, net_pct, regime=self.regime)
            else:
                update_strategy_score(self.strategy, result_str, self.regime)
        except Exception:
            update_strategy_score(self.strategy, result_str, net_pct, regime=self.regime)
        logger.debug(
            "Trade closed: %s %s result=%s net_pct=%.2f",
            self.symbol,
            self.timeframe,
            outcome,
            net_pct,
        )