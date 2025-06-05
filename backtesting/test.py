import MetaTrader5 as mt5
import pandas as pd

mt5.initialize()
rates = mt5.copy_rates_from_pos("XAUUSD.", mt5.TIMEFRAME_M1, 0, 5)
mt5.shutdown()

df = pd.DataFrame(rates)
print(df.columns.tolist())
print(df.head())
