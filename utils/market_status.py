import MetaTrader5 as mt5
from datetime import datetime


def is_market_open(symbol: str) -> bool:
    """Return ``True`` if the market is open for the given symbol."""
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)

    if not info or not getattr(info, "visible", True):
        return False

    trade_mode = getattr(info, "trade_mode", getattr(mt5, "SYMBOL_TRADE_MODE_FULL", 0))
    if trade_mode in (0, 3):
        return False

    if not symbol.startswith(("BTC", "ETH")):
        if not tick or tick.bid == 0.0 or tick.ask == 0.0:
            return False
        if datetime.utcnow().weekday() >= 5:
            return False

    return True