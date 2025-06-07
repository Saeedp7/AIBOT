# connectors/mt5_connector.py

import MetaTrader5 as mt5
from config.manager import get_config

API_LOGIN = int(get_config("MT5_LOGIN", 235934))
API_PASSWORD = get_config("MT5_PASSWORD", "36ca9l!F")
API_SERVER = get_config("MT5_SERVER", "AronMarkets-Demo")
API_PATH = get_config("MT5_PATH", r"C:\\Program Files\\MetaTrader 5\\terminal64.exe")

def initialize_mt5():
    """Initialize MetaTrader5 connection."""
    if not mt5.initialize(path=API_PATH, login=API_LOGIN, password=API_PASSWORD, server=API_SERVER):
        error = mt5.last_error()
        print(f"❌ Failed to initialize MT5: {error}")
        return False
    print("✅ MT5 initialized successfully.")
    return True


def shutdown_mt5():
    """Shutdown MetaTrader5 connection."""
    mt5.shutdown()
    print("🛑 MT5 connection closed.")

def get_account_info():
    if not mt5.initialize():
        raise Exception("❌ Failed to initialize MT5")
    info = mt5.account_info()
    if info is None:
        error = mt5.last_error()
        raise Exception(f"❌ Failed to retrieve account info: {error}")
    return info

def is_connected() -> bool:
    """Check if MT5 is still connected."""
    return mt5.terminal_info() is not None

def symbol_info_tick(symbol: str):
    """Get full symbol info from MT5"""
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"⚠️ Failed to get symbol info for {symbol}")
    return info

def get_symbol_price(symbol: str):
    """Returns the latest bid/ask mid-price for a symbol"""
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        return round((tick.bid + tick.ask) / 2, 2)
    print(f"⚠️ No tick data for {symbol}")
    return None