from __future__ import annotations

"""Utility functions for session-based timing logic."""

from datetime import datetime, time, timezone
from typing import List, Tuple
import logging

from config.manager import get_config

_DEFAULT_SESSIONS = "00:00-03:00;07:00-11:00;13:30-17:00"


def _parse_ranges(ranges: str) -> List[Tuple[time, time]]:
    result: List[Tuple[time, time]] = []
    for part in ranges.split(";"):
        if "-" not in part:
            continue
        start_s, end_s = part.split("-", 1)
        try:
            start = time.fromisoformat(start_s.strip())
            end = time.fromisoformat(end_s.strip())
            result.append((start, end))
        except ValueError:
            continue
    return result


_SESSIONS = _parse_ranges(get_config("SESSION_TIMES", _DEFAULT_SESSIONS))
_OFF_RISK = float(get_config("OFF_SESSION_RISK", 0.5))
_TRADE_OUTSIDE_SESSIONS = get_config("TRADE_OUTSIDE_SESSIONS", "true").lower() == "true"
_REDUCED_RISK_OUTSIDE_SESSION = float(
    get_config("REDUCED_RISK_OUTSIDE_SESSION", _OFF_RISK)
)

logger = logging.getLogger(__name__)

def is_in_high_session(now: datetime | None = None) -> bool:
    """Return ``True`` if ``now`` falls inside a high-volume session."""
    now_dt = datetime.now(timezone.utc)
    now_t = now_dt.time()
    for start, end in _SESSIONS:
        if start <= now_t <= end:
            return True
    return False


def session_risk_multiplier(now: datetime | None = None) -> float:
    """Return risk multiplier depending on high/low session settings."""
    now_dt = datetime.now(timezone.utc)
    if is_in_high_session(now_dt):
        logger.debug(f"Current UTC time: {now_dt}. Session: HIGH.")
        return 1.0
    if _TRADE_OUTSIDE_SESSIONS:
        logger.debug(
            f"Current UTC time: {now_dt}. Session: LOW. Applying {_REDUCED_RISK_OUTSIDE_SESSION * 100:.0f}% risk."
        )
        return _REDUCED_RISK_OUTSIDE_SESSION
    logger.debug(f"Current UTC time: {now_dt}. Session: LOW. Trading disabled.")
    return 0.0