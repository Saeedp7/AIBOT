import pandas as pd
from config.settings import (
    SYMBOL_OVERRIDES,
    USE_ATR_SL,
    ATR_PERIOD,
    ATR_MULTIPLIER,
)
from connectors.mt5_connector import symbol_info_tick
from risk_management.stop_loss_manager import determine_sl_tp
from utils.indicators import calculate_atr

def calculate_position_size_and_targets(entry_price, balance, strategy_name, direction, market_data, risk_percent=1.0, symbol="XAUUSD"):
    fallback = SYMBOL_OVERRIDES.get(symbol, {})
    info = symbol_info_tick(symbol)

    tick_size = getattr(info, "trade_tick_size", 0) or fallback.get("tick_size", 0.01)
    tick_value = getattr(info, "trade_tick_value", 0) or fallback.get("tick_value", 1.0)
    contract_size = getattr(info, "trade_contract_size", 0) or fallback.get("contract_size", 100)

    # Calculate SL and TP levels dynamically using AI/strategy-aware method
    stop_loss, tp_levels, regime = determine_sl_tp(strategy_name, entry_price, direction, market_data)
   # Optionally override stop_loss using ATR-based distance
    if USE_ATR_SL and isinstance(market_data, pd.DataFrame):
        if all(col in market_data.columns for col in ["high", "low", "close"]):
            atr = calculate_atr(market_data, ATR_PERIOD).iloc[-1]
            if pd.notna(atr) and atr > 0:
                sl_offset = atr * ATR_MULTIPLIER
                stop_loss = (
                    entry_price - sl_offset if direction == "buy" else entry_price + sl_offset
                )

    sl_distance = abs(entry_price - stop_loss)
    if tick_size == 0 or tick_value == 0 or sl_distance == 0:
        return 0.01, stop_loss, tp_levels, regime

    sl_ticks = sl_distance / tick_size
    loss_per_lot = sl_ticks * tick_value

    risk_amount = balance * (risk_percent / 100)
    volume = risk_amount / loss_per_lot

    # Round and clamp
    volume = round(volume, 2)
    volume = max(0.01, min(volume, 100.0))

    return volume, stop_loss, tp_levels, regime