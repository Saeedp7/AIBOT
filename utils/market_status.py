from datetime import datetime, time, timedelta
import MetaTrader5 as mt5

def is_market_open(symbol: str) -> bool:
    """Return ``True`` if trading is allowed for ``symbol`` right now."""
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)

    if not info or not getattr(info, "visible", True):
        return False

    full_mode = getattr(mt5, "SYMBOL_TRADE_MODE_FULL", None)
    if full_mode is not None and info.trade_mode not in (full_mode,):
        return False

    if not tick or tick.bid <= 0 or tick.ask <= 0:
        return False

    tick_time = getattr(tick, "time", None)
    if tick_time is None:
        return True

    # Convert broker time (UTC) to Tehran time (UTC+3:30)
    utc_time = datetime.utcfromtimestamp(tick_time)
    tehran_time = utc_time + timedelta(minutes=30)

    current_time = tehran_time.time()
    weekday = tehran_time.weekday()  # Monday = 0, Sunday = 6

    # Define restricted types
    crypto_symbols = {"BTCUSD.", "ETHUSD."}
    is_crypto = symbol in crypto_symbols

    # Weekend check
    is_weekend = weekday >= 5  # Saturday=5, Sunday=6

    # Time range
    session_start = time(1, 30)
    session_end = time(23, 59)

    # === Enforcement ===
    # Disable crypto entirely
    if is_crypto:
        return False

    # Block all trading on weekends
    if is_weekend:
        return False

    if not (session_start <= current_time <= session_end):
        return False

    return True
