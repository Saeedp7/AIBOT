from config.settings import LOT_SIZE
from connectors.mt5_connector import symbol_info_tick


def calculate_lot_size(balance: float, sl_distance: float, risk_percent: float, symbol: str) -> float:
    """Calculate lot size based on SL distance and risk percentage."""
    info = symbol_info_tick(symbol)
    if not info:
        print(f"⚠️ Symbol info for {symbol} not available. Using fallback LOT_SIZE.")
        return LOT_SIZE

    tick_size = getattr(info, "trade_tick_size", 0)
    tick_value = getattr(info, "trade_tick_value", 0)
    contract_size = getattr(info, "trade_contract_size", 0)
    print(f"[DEBUG] Using tick_size={tick_size}, tick_value={tick_value}, contract_size={contract_size}")


    if tick_size <= 0 or tick_value <= 0 or contract_size <= 0:
        print(f"⚠️ Invalid trading parameters for {symbol}. Using fallback LOT_SIZE.")
        return LOT_SIZE

    risk_amount = balance * (risk_percent / 100.0)
    sl_ticks = sl_distance / tick_size
    loss_per_lot = sl_ticks * tick_value * contract_size
    if loss_per_lot <= 0:
        return LOT_SIZE

    volume = risk_amount / loss_per_lot
    volume = round(volume, 2)
    return max(0.01, min(volume, 100.0))


if __name__ == "__main__":
    size = calculate_lot_size(10000, 50, 1.0, "XAUUSD")
    print(f"Calculated lot size: {size}")