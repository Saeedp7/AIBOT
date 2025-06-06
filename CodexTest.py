import MetaTrader5 as mt5
from risk_management.lot_sizing_module import calculate_lot_size

mt5.initialize()  # Must be called here

lot = calculate_lot_size(100100, 10, 3.0, "XAUUSD.")
print("✅ Calculated lot size:", lot)

mt5.shutdown()  # Always close when done
