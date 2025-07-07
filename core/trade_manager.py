"""Central trade lifecycle manager."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

from .risk_evaluator import RiskEvaluator
from .trade_executor import TradeExecutor
from .monitor import Monitor
from monitoring.alert_manager import send_telegram_alert

# Simple container for currently active trades
active_trades: List[dict] = []

@dataclass
class TradeResult:
    ticket: int
    symbol: str
    entry: float
    entry_time: datetime
    strategy: str | None = None
    strategy_type: str = "day"
    tp_levels: List[float] | None = None
    tp_hits: int = 0
    sl_moved: bool = False


class TradeManager:
    """Handle trade validation, execution and journaling."""

    def __init__(self, evaluator: RiskEvaluator | None = None,
                 executor: TradeExecutor | None = None,
                 monitor: Monitor | None = None) -> None:
        self.evaluator = evaluator or RiskEvaluator()
        self.executor = executor or TradeExecutor()
        self.monitor = monitor or Monitor()

    def validate_trade(self, symbol: str, risk_pct: float) -> bool:
        """Check if trade can be placed."""
        # risk_pct -> lot size placeholder
        lot = risk_pct
        return self.evaluator.validate(symbol, lot)

    def execute_trade(
        self,
        symbol: str,
        entry_price: float,
        sl: float,
        tp_list: List[float] | None = None,
        lot: float = 0.01,
        *,
        strategy_name: str = "",
        strategy_type: str = "day",
    ) -> TradeResult:
        ticket = self.executor.execute(symbol, entry_price, lot, sl, tp_list)
        self.monitor.log(
            f"Executed {symbol} at {entry_price} SL={sl} TP={tp_list}"
        )
        tp1 = tp_list[0] if tp_list else 'N/A'
        send_telegram_alert(
            f"\U0001F7E2 Trade Opened\n"
            f"Symbol: {symbol}\n"
            f"Strategy: {strategy_name}\n"
            f"Entry: {entry_price} | SL: {sl} | TP1: {tp1}"
        )
        trade = TradeResult(
            ticket=ticket,
            symbol=symbol,
            entry=entry_price,
            entry_time=datetime.utcnow(),
            strategy=strategy_name,
            strategy_type=strategy_type,
            tp_levels=tp_list or [],
        )
        active_trades.append(trade.__dict__)
        return trade

    def update_after_exit(self, trade_id: int, result: Dict) -> None:
        self.monitor.update(trade_id, result)

    def close_trade(self, trade: Dict) -> None:
        """Remove trade from active list (placeholder for real close logic)."""
        if trade in active_trades:
            active_trades.remove(trade)
        self.monitor.log(f"Closed trade {trade.get('ticket')}")
        send_telegram_alert(
            f"\U0001F534 Trade Closed\nTicket: {trade.get('ticket')} | Reason: {trade.get('exit_reason', 'manual')}"
        )
    def monitor_active_trades(self) -> None:
        for trade in list(active_trades):
            duration = (datetime.utcnow() - trade["entry_time"]).total_seconds() / 60
            timeout = 240 if trade.get("strategy_type") == "scalp" else 1440

            if duration > timeout:
                print(f"⏱️ Auto-closing {trade['strategy']} after {duration:.1f} min")
                trade["exit_reason"] = "timeout_close"
                self.close_trade(trade)
                send_telegram_alert(
                    f"\u23F1\uFE0F Timeout Close\nStrategy: {trade.get('strategy')} | Duration: {duration:.0f}m"
                )

    def update_stop_loss(self, trade: Dict) -> None:
        if "tp_hits" not in trade:
            return

        if trade["tp_hits"] == 1 and not trade.get("sl_moved", False):
            self.modify_sl(trade, new_sl=trade["entry"])
            trade["sl_moved"] = True
            trade["exit_reason"] = "breakeven_locked"
            send_telegram_alert(
                f"\ud83d\udd14 SL moved to breakeven for ticket {trade.get('ticket')}"
            )

        elif trade["tp_hits"] >= 2:
            tp2 = trade["tp_levels"][1]
            new_sl = tp2 - (tp2 - trade["entry"]) * 0.2
            self.modify_sl(trade, new_sl=round(new_sl, 2))
            trade["exit_reason"] = "trailing_sl"
            send_telegram_alert(
                f"\ud83d\udd14 Trailing SL updated for ticket {trade.get('ticket')} -> {round(new_sl, 2)}"
            )

    def modify_sl(self, trade: Dict, new_sl: float) -> None:
        """Placeholder for SL modification call."""
        trade["sl"] = new_sl
        self.monitor.log(f"Modify SL for {trade.get('ticket')} -> {new_sl}")
