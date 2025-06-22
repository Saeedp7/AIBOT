from __future__ import annotations

"""Session guard to block trading during news or illiquid hours."""

from datetime import datetime, time, timezone
from typing import List, Tuple, Optional
import logging

from connectors.mt5_connector import symbol_info_tick
from config.manager import get_config
from utils.time_utils import session_risk_multiplier

_DEFAULT_BLOCK = "22:00-23:59,00:00-01:00"


def _parse_ranges(ranges: str) -> List[Tuple[time, time]]:
    result: List[Tuple[time, time]] = []
    for part in ranges.split(','):
        if '-' not in part:
            continue
        start_s, end_s = part.split('-', 1)
        try:
            start = time.fromisoformat(start_s.strip())
            end = time.fromisoformat(end_s.strip())
            result.append((start, end))
        except ValueError:
            continue
    return result


_BLOCKED = _parse_ranges(get_config("BLOCK_SESSIONS", _DEFAULT_BLOCK))

logger = logging.getLogger(__name__)


def market_is_open(symbol: str) -> Optional[bool]:
    """Return ``True`` if MT5 reports the market for ``symbol`` is tradable."""
    try:
        info = symbol_info_tick(symbol)
    except Exception:
        return None
    if not info:
        return None
    trade_mode = getattr(info, "trade_mode", None)
    if trade_mode is not None:
        # 0 = disabled, 3 = close only
        if trade_mode in (0, 3):
            return False
    return True


def session_allowed(symbol: str, now: datetime | None = None) -> bool:
    """Return ``True`` if trading is allowed for ``symbol`` at ``now`` (UTC)."""
    now_dt = now if now is not None else datetime.now(timezone.utc)
    status = market_is_open(symbol)
    if status is False:
        return False
    multiplier = session_risk_multiplier(now_dt)
    if multiplier == 0.0:
        logger.info("Session guard blocked trading for %s", symbol)
        return False
    if multiplier != 1.0:
        logger.info(
            "Low session active — applying reduced risk multiplier: %s",
            multiplier,
        )
    return True