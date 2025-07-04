"""Central trade lifecycle manager."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from .risk_evaluator import RiskEvaluator
from .trade_executor import TradeExecutor
from .monitor import Monitor


@dataclass
class TradeResult:
    ticket: int
    symbol: str
    entry: float
    direction: str


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
        direction: str,
        symbol: str,
        entry_price: float,
        sl: float,
        tp_list: List[float] | None = None,
        lot: float = 0.01,
    ) -> TradeResult:
        ticket = self.executor.execute(direction, symbol, entry_price, lot, sl, tp_list)
        self.monitor.log(
            f"Executed {symbol} at {entry_price} SL={sl} TP={tp_list}"
        )
        return TradeResult(ticket=ticket, symbol=symbol, entry=entry_price, direction=direction)

    def update_after_exit(self, trade_id: int, result: Dict) -> None:
        self.monitor.update(trade_id, result)
