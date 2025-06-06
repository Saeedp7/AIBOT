from data.data_collection import collect_ohlcv_data
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators

raw = collect_ohlcv_data(symbols=["XAUUSD."], timeframes=["H1"], limit=200)
cleaned = preprocess_ohlcv_data(raw)
enriched = add_indicators(cleaned)
df = enriched["XAUUSD."]["H1"]
print(df.tail())
