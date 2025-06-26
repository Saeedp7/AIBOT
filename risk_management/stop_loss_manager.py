# risk_management/stop_loss_manager.py

import numpy as np
from utils.indicators import calculate_atr
from config.manager import get_config
from config.settings import REGIME_SL_MULTIPLIERS, REGIME_TP_MULTIPLIERS

# Define pip sizes per symbol
PIP_SIZES = {
    "XAUUSD": 0.1,
    "NDXUSD": 1.0,
    "DJIUSD": 1.0,
    "BTCUSD": 1.0,
    "ETHUSD": 1.0,
}

# Default pip distances per TP
TP_PIP_DISTANCES = [40, 80, 120, 160, 200]

def calculate_sl_tp(entry_price, direction, sl_percent=1.5, tp_percent=2.0):
    """Basic SL/TP calculator for fixed %."""
    if direction == 'buy':
        stop_loss = entry_price * (1 - sl_percent / 100)
        take_profit = entry_price * (1 + tp_percent / 100)
    elif direction == 'sell':
        stop_loss = entry_price * (1 + sl_percent / 100)
        take_profit = entry_price * (1 - tp_percent / 100)
    else:
        raise ValueError("Invalid trade direction. Must be 'buy' or 'sell'.")
    return round(stop_loss, 2), round(take_profit, 2)

def determine_sl_tp(
    strategy_name,
    entry_price,
    direction,
    market_data,
    *,
    symbol: str | None = None,
):
    """
    Use AI and regime intelligence to set SL and multi-TPs based on strategy and market context.
    Returns: stop_loss, take_profits (list), regime
    """
    if market_data is None or market_data.empty:
        raise ValueError("Market data is empty or None.")

    from ai_engine.regime_classifier import detect_market_regime

    base_symbol = symbol.replace(".", "") if symbol else "XAUUSD"
    pip_size = PIP_SIZES.get(base_symbol.upper(), 1.0)

    regime = detect_market_regime(market_data, symbol=base_symbol or strategy_name)
    atr_series = calculate_atr(market_data, period=14).dropna()
    atr = float(atr_series.iloc[-1]) if not atr_series.empty else None

    # Determine number of TPs
    if 'scalping' in strategy_name.lower():
        num_tps = 3
    elif 'swing' in strategy_name.lower():
        num_tps = 5
    else:
        num_tps = 4
    if regime == 'volatile':
        num_tps = min(5, num_tps + 1)
    num_tps = max(3, min(num_tps, 5))

    pip_distances = TP_PIP_DISTANCES[:num_tps]

    # Build TP and SL based on fixed pip logic
    multiplier = 1 if direction == "buy" else -1
    take_profits = [
        round(entry_price + multiplier * pip_size * pip, 2) for pip in pip_distances
    ]
    stop_loss = round(entry_price - multiplier * pip_size * pip_distances[0], 2)

    return stop_loss, take_profits, regime

def get_required_timeframes(strategy):
    """Auto-select timeframes based on strategy group"""
    group = getattr(strategy, "strategy_group", "day").lower()
    if group == "scalping":
        return ["M1", "M5", "M15"]
    elif group == "swing":
        return ["M15", "H1", "H4"]
    else:
        return ["M15", "H1", "H4"]  # default to day trading
