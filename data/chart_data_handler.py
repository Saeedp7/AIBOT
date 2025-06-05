# data/chart_data_handler.py

import MetaTrader5 as mt5
import pandas as pd
from config.settings import SYMBOL, TIMEFRAME

# Map timeframe strings to MT5 constants
TIMEFRAME_MAPPING = {
    'M1': mt5.TIMEFRAME_M1,
    'M5': mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'M30': mt5.TIMEFRAME_M30,
    'H1': mt5.TIMEFRAME_H1,
    'H4': mt5.TIMEFRAME_H4,
    'D1': mt5.TIMEFRAME_D1,
}

def get_ohlcv(symbol=SYMBOL, timeframe=TIMEFRAME, start=None, end=None, num_bars=500):
    """Fetch OHLCV historical data with optional date range."""
    tf = TIMEFRAME_MAPPING.get(timeframe)
    if tf is None:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    if start and end:
        start_ts = pd.to_datetime(start)
        end_ts = pd.to_datetime(end)
        rates = mt5.copy_rates_range(symbol, tf, start_ts, end_ts)
    else:
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, num_bars)

    if rates is None or len(rates) == 0:
        raise Exception(f"❌ Failed to fetch rates for {symbol} at {timeframe}")

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    df['volume'] = df['tick_volume']
    df['delta'] = df['volume'].diff().fillna(0)

    return df



def get_latest_price(symbol=SYMBOL):
    """Fetch the latest bid/ask price."""
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise Exception(f"❌ Failed to fetch latest tick for {symbol}")
    return {
        'bid': tick.bid,
        'ask': tick.ask,
        'last': (tick.bid + tick.ask) / 2
    }
