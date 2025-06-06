# data/chart_data_handler.py

import MetaTrader5 as mt5
import pandas as pd
import requests
import os
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

# Map timeframe strings to Binance intervals
BINANCE_TIMEFRAME_MAPPING = {
    'M1': '1m',
    'M5': '5m',
    'M15': '15m',
    'M30': '30m',
    'H1': '1h',
    'H4': '4h',
    'D1': '1d',
}

def get_ohlcv(symbol=SYMBOL, timeframe=TIMEFRAME, start=None, end=None, num_bars=500):
    """Fetch OHLCV data from MT5 with optional date range."""
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
        'last': (tick.bid + tick.ask) / 2,
    }



def get_binance_ohlcv(symbol, timeframe, start=None, end=None, limit=500):
    """Fetch OHLCV data from Binance public REST API."""
    interval = BINANCE_TIMEFRAME_MAPPING.get(timeframe)
    if interval is None:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    url = 'https://api.binance.com/api/v3/klines'
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit,
    }

    if start:
        params['startTime'] = int(pd.to_datetime(start).timestamp() * 1000)
    if end:
        params['endTime'] = int(pd.to_datetime(end).timestamp() * 1000)

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    raw = response.json()

    columns = [
        'open_time',
        'open',
        'high',
        'low',
        'close',
        'volume',
        'close_time',
        'quote_asset_volume',
        'number_of_trades',
        'taker_base_vol',
        'taker_quote_vol',
        'ignore',
    ]
    df = pd.DataFrame(raw, columns=columns)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df.set_index('open_time', inplace=True)
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].astype(float)
    df['delta'] = df['volume'].diff().fillna(0)
    return df


def load_multi_ohlcv(symbols, timeframes, source='MT5', start=None, end=None, num_bars=500, to_csv=False, csv_dir='data/historical'):
    """Load OHLCV data for multiple symbols/timeframes from MT5 or Binance."""
    data = {}
    if to_csv:
        os.makedirs(csv_dir, exist_ok=True)

    for symbol in symbols:
        data[symbol] = {}
        for tf in timeframes:
            if source.upper() == 'BINANCE':
                df = get_binance_ohlcv(symbol, tf, start=start, end=end, limit=num_bars)
            else:
                df = get_ohlcv(symbol, tf, start=start, end=end, num_bars=num_bars)
            data[symbol][tf] = df
            if to_csv:
                filename = f"{symbol}_{tf}.csv".replace('/', '')
                df.to_csv(os.path.join(csv_dir, filename))

    return data