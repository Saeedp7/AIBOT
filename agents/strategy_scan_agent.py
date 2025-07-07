from __future__ import annotations

import json
from typing import Iterable, List, Dict

from config.manager import get_config
from strategies.strategy_selector import StrategySelector
from agents.market_scanner_agent import MarketScannerAgent
from agents.strategy_evaluator_agent import StrategyEvaluatorAgent
from agents.regime_filter import filter_strategies

class StrategyScanAgent:
    """Scan all strategies for multiple symbols and timeframes."""

    def __init__(self, strategies: Iterable = None) -> None:
        if strategies is None:
            strategies = StrategySelector().strategies
        self.strategies = list(strategies)
        self.scanner = MarketScannerAgent()
        self.evaluator = StrategyEvaluatorAgent()

    def scan(self, symbols: Iterable[str]) -> List[Dict]:
        """Run all strategies over symbols respecting preferred timeframes."""
        results: List[Dict] = []
        for symbol in symbols:
            for strat in self.strategies:
                tfs = getattr(strat, "preferred_tf", "M15")
                if not isinstance(tfs, (list, tuple)):
                    tfs = [tfs]
                for tf in tfs:
                    df, regime = self.scanner.scan(symbol, tf)
                    if df is None:
                        continue
                    allowed = filter_strategies([strat], regime)
                    if not allowed:
                        continue
                    evaluation = self.evaluator.evaluate(allowed, df, regime, symbol=symbol, timeframe=tf)
                    signal = evaluation[0]["signal"] if evaluation else None
                    score = evaluation[0]["score"] if evaluation else None
                    results.append(
                        {
                            "symbol": symbol,
                            "strategy": strat.__class__.__name__,
                            "timeframe": tf,
                            "regime": regime,
                            "signal": signal,
                            "score": score,
                        }
                    )
        return results


def main() -> None:
    symbols = get_config("SYMBOLS", "XAUUSD.,NDXUSD.,DJIUSD.").split(",")
    agent = StrategyScanAgent()
    results = agent.scan(symbols)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()