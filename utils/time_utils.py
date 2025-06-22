from __future__ import annotations

"""Utility functions for session-based timing logic."""

from datetime import datetime, time, timezone
from typing import List, Tuple

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


def in_active_session(now: datetime | None = None) -> bool:
    """Return ``True`` if ``now`` (UTC) falls within any configured session."""
    now_t = (now or datetime.now(timezone.utc)).time()
    for start, end in _SESSIONS:
        if start <= now_t <= end:
            return True
    return False


def session_risk_multiplier(now: datetime | None = None) -> float:
    """Return risk multiplier based on whether we are in an active session."""
    return 1.0 if in_active_session(now) else _OFF_RISK