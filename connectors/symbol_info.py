from dataclasses import dataclass
import MetaTrader5 as mt5

@dataclass
class SymbolSpecs:
    tick_size: float
    tick_value: float
    digits: int | None = None

def get_symbol_specs(symbol: str) -> SymbolSpecs:
    """Retrieve tick size and tick value for a trading symbol."""
    info = mt5.symbol_info(symbol)
    tick_size = getattr(info, "trade_tick_size", 0) if info else 0
    tick_value = getattr(info, "trade_tick_value", 0) if info else 0
    digits = getattr(info, "digits", None) if info else None
    return SymbolSpecs(tick_size=tick_size, tick_value=tick_value, digits=digits)