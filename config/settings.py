# config/settings.py

import os
from itertools import product
from config.manager import get_config

# --- Broker API Credentials ---
API_LOGIN = int(os.getenv('MT5_LOGIN', 245905))
API_PASSWORD = os.getenv('MT5_PASSWORD', '09ba5x!L')
API_SERVER = os.getenv('MT5_SERVER', 'AronMarkets-Demo')
API_PATH = os.getenv('MT5_PATH', r'C:\Program Files\MetaTrader 5\terminal64.exe')

# --- Trading Settings ---
# config/settings.py
SYMBOLS = ["XAUUSD.", "NDXUSD.", "DJIUSD."]
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
LIVE_MODE = os.getenv('LIVE_MODE', 'true').lower() == 'true'
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

# --- Regime detection thresholds ---
REGIME_ATR_SLOPE_THRESHOLD = float(os.getenv("REGIME_ATR_SLOPE_THRESHOLD", 0.7))
REGIME_EMA_DISTANCE_THRESHOLD = float(os.getenv("REGIME_EMA_DISTANCE_THRESHOLD", 0.5))
EMA_SLOPE_THRESHOLD = float(os.getenv("EMA_SLOPE_THRESHOLD", 0.1))
ATR_VOLATILITY_THRESHOLD = float(os.getenv("ATR_VOLATILITY_THRESHOLD", 20.0))
STRUCTURE_LOOKBACK = int(os.getenv("STRUCTURE_LOOKBACK", 3))

# --- Debug / Filter Tweaks ---
MIN_REWARD_TO_RISK = float(os.getenv("MIN_REWARD_TO_RISK", 1.2))
ALLOW_RANGING_ENTRIES = os.getenv("ALLOW_RANGING_ENTRIES", "true").lower() == "true"
BOLLINGER_FILTER_ENABLED = os.getenv("BOLLINGER_FILTER_ENABLED", "false").lower() == "true"

# --- Regime-based SL/TP multipliers ---
REGIME_SL_MULTIPLIERS = {
    "volatile": float(os.getenv("VOLATILE_SL_MULTIPLIER", 1.5)),
    "trending": float(os.getenv("TRENDING_SL_MULTIPLIER", 0.8)),
    "ranging": float(os.getenv("RANGING_SL_MULTIPLIER", 1.0)),
}

REGIME_TP_MULTIPLIERS = {
    "volatile": float(os.getenv("VOLATILE_TP_MULTIPLIER", 0.8)),
    "trending": float(os.getenv("TRENDING_TP_MULTIPLIER", 1.5)),
    "ranging": float(os.getenv("RANGING_TP_MULTIPLIER", 1.0)),
}

# Partial position close ratios (e.g. "0.33,0.33,0.34")
PARTIAL_CLOSE_RATIOS = [
    float(x)
    for x in os.getenv("PARTIAL_CLOSE_RATIOS", "0.33,0.33,0.34").split(",")
    if x
]
# Buffer (in price units) added when moving SL to breakeven after TP1
SL_BUFFER_AFTER_TP1 = float(
    os.getenv("SL_BUFFER_AFTER_TP1", get_config("sl_buffer_after_tp1", 0.5))
)

# --- Confidence thresholds and risk scaling ---
import json

_raw_thresh = os.getenv("DEFAULT_CONFIDENCE_THRESHOLDS", None)
if _raw_thresh is None:
    _raw_thresh = get_config(
        "default_confidence_thresholds",
        '{"trending": 0.3, "ranging": 0.15, "volatile": 0.25}',
    )
if isinstance(_raw_thresh, str):
    DEFAULT_CONFIDENCE_THRESHOLDS = json.loads(_raw_thresh)
else:
    DEFAULT_CONFIDENCE_THRESHOLDS = _raw_thresh
MIN_RISK_SCALE = float(
    os.getenv("MIN_RISK_SCALE", get_config("min_risk_scale", 0.3))
)

DEFAULT_ALLOWED_REGIMES = ["trending", "volatile"]
if ALLOW_RANGING_ENTRIES:
    DEFAULT_ALLOWED_REGIMES.append("ranging")