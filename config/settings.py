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
TIMEFRAMES = ["M5", "M15", "H1", "H4"]
SYMBOL = os.getenv('TRADE_SYMBOL', 'XAUUSD.')
CHECK_INTERVAL_SECONDS = 60
TIMEFRAME = os.getenv('TRADE_TIMEFRAME', 'M5')  # Default to 1-minute
LOT_SIZE = float(os.getenv('LOT_SIZE', 0.1))

# --- Risk Management Settings ---
MAX_RISK_PER_TRADE = float(os.getenv('MAX_RISK', 0.01))  # 1% default
STOP_LOSS_MULTIPLIER = float(os.getenv('SL_MULTIPLIER', 1.5))
TAKE_PROFIT_MULTIPLIER = float(os.getenv('TP_MULTIPLIER', 2.0))

# --- Misc Settings ---
MAGIC_NUMBER = int(os.getenv('MAGIC_NUMBER', 123456))

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