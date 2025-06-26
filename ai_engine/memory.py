import json
import os
from typing import Dict

class StrategyMemory:
    """Simple persistence for per-context strategy scores."""

    def __init__(self, path: str = "ai_engine/strategy_memory.json") -> None:
        self.path = path
        self.data: Dict[str, Dict] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def update_score(
        self,
        *,
        symbol: str,
        timeframe: str,
        strategy: str,
        regime: str,
        score_delta: float,
    ) -> None:
        sym_map = self.data.setdefault(symbol, {})
        tf_map = sym_map.setdefault(timeframe, {})
        strat_map = tf_map.setdefault(strategy, {})
        key = regime or "unknown"
        strat_map[key] = float(strat_map.get(key, 0.0)) + float(score_delta)
        self._save()


strategy_memory = StrategyMemory()
