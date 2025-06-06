from data.data_collection import collect_ohlcv_data
data = collect_ohlcv_data(
    symbols=["XAUUSD.", "BTCUSD."],
    timeframes=["M5", "H1"],
    limit=200
)
for sym, tfs in data.items():
    for tf, df in tfs.items():
        print(sym, tf, len(df))
