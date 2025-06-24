import MetaTrader5 as mt5
from datetime import datetime, time, timedelta


def is_market_open(symbol: str) -> bool:
    """Return True if market is open for the given symbol based on Tehran time (01:35–23:30, Mon–Fri)."""
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)

    if not info or not getattr(info, "visible", True):
        return False

    if info.trade_mode not in (mt5.SYMBOL_TRADE_MODE_FULL,):
        return False

    if not tick or tick.bid <= 0 or tick.ask <= 0 or not tick.time:
        return False

    # Convert broker time (UTC) to Tehran time (UTC+3:30)
    utc_time = datetime.utcfromtimestamp(tick.time)
    tehran_offset = timedelta(minutes=30)
    tehran_time = utc_time + tehran_offset

    current_time = tehran_time.time()
    weekday = tehran_time.weekday()  # Monday = 0

    session_start = time(1, 30)
    session_end = time(23, 30)

    if weekday >= 5:
        return False

    if not (session_start <= current_time <= session_end):
        return False

    return True
