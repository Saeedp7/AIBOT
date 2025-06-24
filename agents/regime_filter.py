from __future__ import annotations

from typing import Iterable, List

from strategies.base import BaseStrategy


def filter_strategies(strategies: Iterable[BaseStrategy], regime: str) -> List[BaseStrategy]:
    """Return strategies compatible with ``regime``.

    Each strategy may define ``regimes`` attribute listing allowed regimes.
    If undefined, the strategy is always allowed.
    """
    result: List[BaseStrategy] = []
    for strat in strategies:
        if hasattr(strat, "allowed_regimes"):
            allowed = strat.allowed_regimes()
        else:
            allowed = getattr(strat, "regimes", None)
        if allowed and regime not in allowed:
            continue
        result.append(strat)
    return result