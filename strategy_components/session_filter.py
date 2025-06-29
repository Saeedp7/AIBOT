from __future__ import annotations

"""Session and killzone detection helpers."""

from datetime import datetime, time, timezone
import pandas as pd


LONDON_OPEN = (time(7, 0), time(10, 0))
NEWYORK_OPEN = (time(12, 0), time(15, 0))
NEWYORK_PM = (time(18, 0), time(21, 0))


def in_killzone(ts: datetime) -> bool:
    """Return True if ``ts`` falls within defined killzones (UTC)."""
    t = ts.time()
    return any(start <= t <= end for start, end in (LONDON_OPEN, NEWYORK_OPEN, NEWYORK_PM))


def killzone_label(ts: datetime) -> str:
    """Return human-readable killzone label for ``ts``."""
    t = ts.time()
    if LONDON_OPEN[0] <= t <= LONDON_OPEN[1]:
        return "London AM"
    if NEWYORK_OPEN[0] <= t <= NEWYORK_OPEN[1]:
        return "NY Open"
    if NEWYORK_PM[0] <= t <= NEWYORK_PM[1]:
        return "NY PM"
    return "Off"


def detect_session_high_low_sweep(candles: pd.DataFrame) -> bool:
    """Detect wick sweeps of session highs or lows."""
    if candles.empty:
        return False
    today = candles.index[-1].date()
    today_data = candles.loc[candles.index.date == today]
    if len(today_data) < 2:
        return False
    session_high = today_data["high"].max()
    session_low = today_data["low"].min()
    last = today_data.iloc[-1]
    return last["high"] >= session_high or last["low"] <= session_low


def detect_ndog_nwog(candles: pd.DataFrame) -> bool:
    """Detect New Day Opening Gap / New Week Opening Gap."""
    if len(candles) < 2:
        return False
    prev_close = candles["close"].iloc[-2]
    curr_open = candles["open"].iloc[-1]
    return abs(curr_open - prev_close) > 2 * (candles["high"].iloc[-2] - candles["low"].iloc[-2])