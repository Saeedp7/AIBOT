"""Utilities for fetching OHLCV data from MT5 or Binance."""

from __future__ import annotations

import os
import pandas as pd

try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None

try:
    import MetaTrader5 as mt5
except Exception:  # pragma: no cover - optional dependency
    mt5 = None

from config.manager import get_config

SYMBOL = get_config("TRADE_SYMBOL", "BTCUSD.")
TIMEFRAME = get_config("TRADE_TIMEFRAME", "M5")

TIMEFRAME_MAPPING = {
    "M1": getattr(mt5, "TIMEFRAME_M1", 1),
    "M5": getattr(mt5, "TIMEFRAME_M5", 5),
    "M15": getattr(mt5, "TIMEFRAME_M15", 15),
    "M30": getattr(mt5, "TIMEFRAME_M30", 30),
    "H1": getattr(mt5, "TIMEFRAME_H1", 60),
    "H4": getattr(mt5, "TIMEFRAME_H4", 240),
    "D1": getattr(mt5, "TIMEFRAME_D1", 1440),
}

BINANCE_TIMEFRAME_MAPPING = {
    "M1": "1m",
    "M5": "5m",
    "M15": "15m",
    "M30": "30m",
    "H1": "1h",
    "H4": "4h",
    "D1": "1d",
}


def get_ohlcv(symbol: str = SYMBOL, timeframe: str = TIMEFRAME, start=None, end=None, num_bars: int = 500) -> pd.DataFrame:
    """Fetch OHLCV data from MT5 with optional date range."""
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package not available")
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
        raise RuntimeError(f"Failed to fetch rates for {symbol} {timeframe}")
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    df["volume"] = df["tick_volume"]
    df["delta"] = df["volume"].diff().fillna(0)
    return df


def get_binance_ohlcv(symbol: str, timeframe: str, start=None, end=None, limit: int = 500) -> pd.DataFrame:
    if requests is None:
        raise RuntimeError("requests package not available")
    interval = BINANCE_TIMEFRAME_MAPPING.get(timeframe)
    if not interval:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start:
        params["startTime"] = int(pd.to_datetime(start).timestamp() * 1000)
    if end:
        params["endTime"] = int(pd.to_datetime(end).timestamp() * 1000)
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    raw = resp.json()
    cols = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_base_vol",
        "taker_quote_vol",
        "ignore",
    ]
    df = pd.DataFrame(raw, columns=cols)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df.set_index("open_time", inplace=True)
    num_cols = ["open", "high", "low", "close", "volume"]
    df[num_cols] = df[num_cols].astype(float)
    df["delta"] = df["volume"].diff().fillna(0)
    return df


def load_multi_ohlcv(symbols, timeframes, source="MT5", start=None, end=None, num_bars: int = 500, to_csv: bool = False, csv_dir: str = "data/historical"):
    """Load OHLCV data for multiple symbols/timeframes."""
    data = {}
    if to_csv:
        os.makedirs(csv_dir, exist_ok=True)
    for symbol in symbols:
        data[symbol] = {}
        for tf in timeframes:
            if source.upper() == "BINANCE":
                df = get_binance_ohlcv(symbol, tf, start=start, end=end, limit=num_bars)
            else:
                df = get_ohlcv(symbol, tf, start=start, end=end, num_bars=num_bars)
            data[symbol][tf] = df
            if to_csv:
                filename = f"{symbol}_{tf}.csv".replace("/", "")
                df.to_csv(os.path.join(csv_dir, filename))
    return data
