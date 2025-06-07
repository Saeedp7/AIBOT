# config/settings.py

import os
from itertools import product

# --- Broker API Credentials ---
API_LOGIN = int(os.getenv('MT5_LOGIN', 235934))
API_PASSWORD = os.getenv('MT5_PASSWORD', '36ca9l!F')
API_SERVER = os.getenv('MT5_SERVER', 'AronMarkets-Demo')
API_PATH = os.getenv('MT5_PATH', r'C:\Program Files\MetaTrader 5\terminal64.exe')

# --- Trading Settings ---
# config/settings.py
SYMBOLS = ["XAUUSD.", "BTCUSD.", "ETHUSD.", "NDXUSD.", "DJIUSD."]
TIMEFRAMES = ["M1", "M5", "M15", "H1", "H4"]
SYMBOL = os.getenv('TRADE_SYMBOL', 'BTCUSD.')
CHECK_INTERVAL_SECONDS = 60
TIMEFRAME = os.getenv('TRADE_TIMEFRAME', 'M5')  # Default to 1-minute
LOT_SIZE = float(os.getenv('LOT_SIZE', 0.1))

# --- Risk Management Settings ---
MAX_RISK_PER_TRADE = float(os.getenv('MAX_RISK', 0.01))  # 1% default
STOP_LOSS_MULTIPLIER = float(os.getenv('SL_MULTIPLIER', 1.5))
TAKE_PROFIT_MULTIPLIER = float(os.getenv('TP_MULTIPLIER', 2.0))
DAILY_LOSS_LIMIT_PERCENT = float(os.getenv('DAILY_LOSS_LIMIT_PERCENT', 5.0))
MAX_TRADES_PER_DAY = int(os.getenv('MAX_TRADES_PER_DAY', 20))

# --- Misc Settings ---
MAGIC_NUMBER = int(os.getenv('MAGIC_NUMBER', 123456))
# Toggle real order execution. The LIVE_MODE environment variable should be
# set to 'true' or 'false'. Any value other than 'true' is treated as False.
LIVE_MODE = os.getenv('LIVE_MODE', 'false').lower() == 'true'
# --- Optional fallback per-symbol overrides (future extension) ---
SYMBOL_OVERRIDES = {
    "XAUUSD.": {
        "tick_size": 0.01,
        "tick_value": 1.0,
        "contract_size": 100
    },
    "BTCUSD.": {
        "tick_size": 0.01,
        "tick_value": 1.0,
        "contract_size": 1
    }
}

ACTIVE_SYMBOLS_TIMEFRAMES = {symbol: TIMEFRAMES for symbol in SYMBOLS}

# Backtest date range
BACKTEST_START_DATE = "2025-06-01"
BACKTEST_END_DATE = "2025-06-06"

# --- ATR-based SL Settings ---
USE_ATR_SL = True
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5