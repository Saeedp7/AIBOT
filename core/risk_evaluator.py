"""Simple wrapper around RiskManagerAgent."""

from __future__ import annotations

from agents.risk_manager_agent import RiskManagerAgent


class RiskEvaluator:
    """Validate trades using RiskManagerAgent."""

    def __init__(self) -> None:
        self.agent = RiskManagerAgent()

    def validate(self, symbol: str, lot: float) -> bool:
        ok, _ = self.agent.validate_trade(symbol, lot)
        return ok
