from data.data_collection import collect_ohlcv_data
from data.preprocessing import preprocess_ohlcv_data

# Step 1: Collect raw data
raw_data = collect_ohlcv_data(
    symbols=["XAUUSD.", "BTCUSD."],
    timeframes=["M5", "H1"],
    limit=200
)

# Step 2: Preprocess
cleaned_data = preprocess_ohlcv_data(raw_data)

# Step 3: Print results
for symbol, tf_dict in cleaned_data.items():
    for tf, df in tf_dict.items():
        print(f"{symbol} {tf} index type: {type(df.index)}")
        print(f"{symbol} {tf} head:\n{df.head(2)}")
