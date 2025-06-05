# utils/indicators.py

import pandas as pd
import numpy as np


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()

def calculate_vwap(data: pd.DataFrame) -> pd.Series:
    cumulative_vp = (data['close'] * data['volume']).cumsum()
    cumulative_volume = data['volume'].cumsum()
    return cumulative_vp / cumulative_volume

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(series: pd.Series, fast_period=12, slow_period=26, signal_period=9):
    ema_fast = calculate_ema(series, fast_period)
    ema_slow = calculate_ema(series, slow_period)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    obv = [0]
    for i in range(1, len(close)):
        if close[i] > close[i - 1]:
            obv.append(obv[-1] + volume[i])
        elif close[i] < close[i - 1]:
            obv.append(obv[-1] - volume[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=close.index)

def calculate_fibonacci_levels(high: float, low: float):
    diff = high - low
    return {
        '0.236': high - 0.236 * diff,
        '0.382': high - 0.382 * diff,
        '0.5': high - 0.5 * diff,
        '0.618': high - 0.618 * diff,
        '0.786': high - 0.786 * diff,
    }

def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = data['high'] - data['low']
    high_close = abs(data['high'] - data['close'].shift())
    low_close = abs(data['low'] - data['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def calculate_supertrend(data: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    hl2 = (data['high'] + data['low']) / 2
    atr = calculate_atr(data, period)
    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    direction = []
    prev_dir = 1

    for i in range(len(data)):
        if i == 0:
            direction.append(prev_dir)
            continue

        close = data['close'].iloc[i]
        if close > upperband.iloc[i - 1]:
            curr_dir = 1
        elif close < lowerband.iloc[i - 1]:
            curr_dir = -1
        else:
            curr_dir = prev_dir

        direction.append(curr_dir)
        prev_dir = curr_dir

    return pd.Series(direction, index=data.index)


def calculate_adx(data: pd.DataFrame, di_length: int = 7, adx_smoothing: int = 7) -> pd.Series:
    up_move = data['high'].diff()
    down_move = -data['low'].diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    tr = pd.concat([
        data['high'] - data['low'],
        abs(data['high'] - data['close'].shift()),
        abs(data['low'] - data['close'].shift())
    ], axis=1).max(axis=1)

    tr_smooth = pd.Series(tr).rolling(di_length).mean()
    plus_di = 100 * pd.Series(plus_dm).rolling(di_length).mean() / tr_smooth
    minus_di = 100 * pd.Series(minus_dm).rolling(di_length).mean() / tr_smooth

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(adx_smoothing).mean()
    return adx


def calculate_multi_rsi(data: pd.Series, periods: list) -> dict:
    rsi_dict = {}
    for period in periods:
        rsi_dict[f"rsi_{period}"] = calculate_rsi(data, period)
    return rsi_dict