"""Parallel strategy signal evaluation."""

from __future__ import annotations

import asyncio
from typing import Iterable, List, Dict, Any

from strategies.base import BaseStrategy


class SignalProcessor:
    """Evaluate strategy signals asynchronously."""

    def __init__(self, strategies: Iterable[BaseStrategy]):
        self.strategies = list(strategies)

    async def evaluate(self, data) -> List[Dict[str, Any]]:
        """Return list of evaluations with strategy name and signal result."""

        async def _run(strategy: BaseStrategy):
            return strategy.__class__.__name__, await asyncio.to_thread(
                strategy.generate_signal, data
            )

        tasks = [_run(s) for s in self.strategies]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        evaluations = []
        for name, res in results:
            evaluations.append({"strategy": name, "signal": res})
        return evaluations
