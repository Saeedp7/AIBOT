"""Guard against excessive exposure when stacking trades."""

from __future__ import annotations

from typing import Dict, List


TIMEFRAME_WEIGHTS: Dict[str, int] = {
    "M1": 1,
    "M5": 2,
    "M15": 3,
    "H1": 4,
    "H4": 5,
}

MAX_EXPOSURE_WEIGHT = 6


class ExposureGuard:
    """Simple in-memory exposure tracker."""

    def __init__(self, *, max_weight: int = MAX_EXPOSURE_WEIGHT,
                 weights: Dict[str, int] | None = None) -> None:
        self.max_weight = max_weight
        self.weights = weights or TIMEFRAME_WEIGHTS
        self.positions: Dict[str, List[Dict[str, float | str]]] = {}

    # -----------------------------------------------------
    def _weight(self, symbol: str) -> int:
        return sum(self.weights.get(p["timeframe"], 0) for p in self.positions.get(symbol, []))

    # -----------------------------------------------------
    def allow(self, symbol: str, timeframe: str, direction: str, confidence: float) -> bool:
        """Return ``True`` if a trade can be opened."""

        # weight limit check
        new_weight = self._weight(symbol) + self.weights.get(timeframe, 0)
        if new_weight > self.max_weight:
            return False

        for p in self.positions.get(symbol, []):
            # direction conflict
            if p["direction"] != direction:
                return False
            # duplicate with lower confidence
            if p["timeframe"] == timeframe and p["direction"] == direction and p["confidence"] >= confidence:
                return False
        return True

    # -----------------------------------------------------
    def record(self, symbol: str, timeframe: str, direction: str, confidence: float) -> None:
        """Record a newly opened trade."""

        self.positions.setdefault(symbol, []).append(
            {
                "timeframe": timeframe,
                "direction": direction,
                "confidence": confidence,
            }
        )

    # -----------------------------------------------------
    def remove(self, symbol: str, timeframe: str) -> None:
        """Remove a closed trade from tracking."""

        if symbol not in self.positions:
            return
        self.positions[symbol] = [p for p in self.positions[symbol] if p["timeframe"] != timeframe]
        if not self.positions[symbol]:
            self.positions.pop(symbol, None)
