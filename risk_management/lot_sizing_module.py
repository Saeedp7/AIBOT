import pandas as pd
from config.manager import get_config

LOT_SIZE = float(get_config("LOT_SIZE", 0.1))
USE_ATR_SL = get_config("USE_ATR_SL", "True").lower() == "true"
ATR_PERIOD = int(get_config("ATR_PERIOD", 14))
ATR_MULTIPLIER = float(get_config("ATR_MULTIPLIER", 1.5))
from connectors.mt5_connector import symbol_info_tick
from utils.indicators import calculate_atr

def calculate_lot_size(
    balance: float,
    sl_distance: float,
    risk_percent: float,
    symbol: str,
    market_data: pd.DataFrame | None = None,
) -> float:
    """Calculate lot size based on SL distance and risk percentage."""
    import logging
    logger = logging.getLogger(__name__)
    info = symbol_info_tick(symbol)
    if not info:
        logger.warning(
            "Symbol info for %s not available. Using fallback LOT_SIZE.", symbol
        )
        return LOT_SIZE

    tick_size = getattr(info, "trade_tick_size", 0)
    tick_value = getattr(info, "trade_tick_value", 0)
    contract_size = getattr(info, "trade_contract_size", 0)
    logger.debug(
        "Lot sizing params: tick_size=%s tick_value=%s contract_size=%s",
        tick_size,
        tick_value,
        contract_size,
    )


    if tick_size <= 0 or tick_value <= 0 or contract_size <= 0:
        logger.warning(
            "Invalid trading parameters for %s. Using fallback LOT_SIZE.", symbol
        )
        return LOT_SIZE
   
    # Optionally use ATR to override SL distance
    if USE_ATR_SL and isinstance(market_data, pd.DataFrame):
        if all(col in market_data.columns for col in ["high", "low", "close"]):
            atr = calculate_atr(market_data, ATR_PERIOD).iloc[-1]
            if pd.notna(atr) and atr > 0:
                sl_distance = atr * ATR_MULTIPLIER

    risk_amount = balance * (risk_percent / 100.0)
    sl_ticks = sl_distance / tick_size
    loss_per_lot = sl_ticks * tick_value * contract_size
    if loss_per_lot <= 0:
        return LOT_SIZE

    volume = risk_amount / loss_per_lot
    volume = round(volume, 2)
    volume = max(0.01, min(volume, 100.0))
    logger.debug(
        "Calculated lot size %.2f with sl_distance=%.2f risk_percent=%.2f",
        volume,
        sl_distance,
        risk_percent,
    )
    return volume


if __name__ == "__main__":
    size = calculate_lot_size(10000, 50, 1.0, "XAUUSD")
    print(f"Calculated lot size: {size}")