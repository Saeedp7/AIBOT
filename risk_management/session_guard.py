from __future__ import annotations

"""Session guard to block trading during news or illiquid hours."""

from datetime import datetime, time, timezone
from typing import List, Tuple

from config.manager import get_config

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


def session_allowed(now: datetime | None = None) -> bool:
    """Return ``True`` if trading is allowed at ``now`` (UTC)."""
    now_t = (now or datetime.now(timezone.utc)).time()
    for start, end in _BLOCKED:
        if start <= now_t <= end:
            return False
    return True