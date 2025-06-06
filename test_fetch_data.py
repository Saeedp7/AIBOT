import MetaTrader5 as mt5
from datetime import datetime

symbol = "XAUUSD."
timeframe = mt5.TIMEFRAME_H1
num_bars = 200

# ✅ Connect to MT5
if not mt5.initialize():
    raise Exception(f"MT5 init failed: {mt5.last_error()}")

# ✅ Ensure symbol is visible
if not mt5.symbol_select(symbol, True):
    raise Exception(f"Symbol '{symbol}' not available or not selected.")

# ✅ Fetch data
rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_bars)

# ✅ Disconnect
mt5.shutdown()

# ✅ Check result
if rates is None or len(rates) == 0:
    raise Exception(f"❌ No data fetched for {symbol} on {timeframe}")
else:
    print(f"✅ Successfully fetched {len(rates)} bars.")
    print(rates[:5])  # Show sample
