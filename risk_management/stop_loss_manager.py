# risk_management/stop_loss_manager.py

import numpy as np

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

def determine_sl_tp(strategy_name, entry_price, direction, market_data):
    """
    Use AI and regime intelligence to set SL and multi-TPs based on strategy and market context.
    Also returns the regime ('trending', 'volatile', 'ranging').
    """
    if market_data is None or market_data.empty:
        raise ValueError("Market data is empty or None.")

    volatility = np.std(market_data['close'].pct_change().dropna()) * 100
    trend_strength = abs(market_data['close'].iloc[-1] - market_data['close'].iloc[-20]) / market_data['close'].iloc[-20]

    if trend_strength > 0.015:
        regime = 'trending'
    elif volatility > 1.5:
        regime = 'volatile'
    else:
        regime = 'ranging'

    if 'scalping' in strategy_name.lower():
        sl_pips = 3.0
        tp_steps = [3, 5, 7, 10, 15]
    elif 'swing' in strategy_name.lower():
        sl_pips = 30.0
        tp_steps = [30, 50, 75, 100, 120]
    else:  # day trading
        sl_pips = 10.0
        tp_steps = [10, 20, 30, 40, 50]

    multiplier = 1 if direction == 'buy' else -1
    stop_loss = round(entry_price - multiplier * sl_pips, 2)
    take_profits = [round(entry_price + multiplier * tp, 2) for tp in tp_steps]

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
