def is_market_open(symbol: str) -> bool:
    """Return True if market is open for the given symbol based on Tehran time (01:30–23:59, Mon–Fri)."""
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

    # Define symbol type
    crypto_symbols = {"BTCUSD.", "ETHUSD."}
    is_crypto = symbol in crypto_symbols

    # Weekend check
    is_weekend = weekday >= 5  # Saturday=5, Sunday=6

    # Time range
    session_start = time(1, 30)
    session_end = time(23, 59)

    # === Enforcement ===
    if is_crypto and not is_weekend:
        return False  # Crypto allowed only on weekend
    if not is_crypto and is_weekend:
        return False  # Forex/indices allowed only on weekdays
    if not (session_start <= current_time <= session_end):
        return False

    return True
