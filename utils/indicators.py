import pandas as pd
import numpy as np
import talib


def calculate_ema(series, period):
    return talib.EMA(series, timeperiod=period)


def calculate_sma(series, period):
    return talib.SMA(series, timeperiod=period)


def calculate_rsi(series, period=14):
    return talib.RSI(series, timeperiod=period)


def calculate_macd(series):
    macd, signal, hist = talib.MACD(series, fastperiod=12, slowperiod=26, signalperiod=9)
    return macd, signal, hist


def calculate_vwap(df):
    return ((df['high'] + df['low'] + df['close']) / 3 * df['volume']).cumsum() / df['volume'].cumsum()


def calculate_bollinger_bands(series, period=20, dev=2):
    upper, middle, lower = talib.BBANDS(series, timeperiod=period, nbdevup=dev, nbdevdn=dev, matype=0)
    return upper, middle, lower


def calculate_adx(df, period=14):
    return talib.ADX(df['high'], df['low'], df['close'], timeperiod=period)


def calculate_supertrend(df, period=10, multiplier=3):
    hl2 = (df['high'] + df['low']) / 2
    atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=period)

    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    supertrend = [True] * len(df)

    for i in range(1, len(df)):
        if df['close'][i] > upperband[i - 1]:
            supertrend[i] = True
        elif df['close'][i] < lowerband[i - 1]:
            supertrend[i] = False
        else:
            supertrend[i] = supertrend[i - 1]

            if supertrend[i] and lowerband[i] < lowerband[i - 1]:
                lowerband[i] = lowerband[i - 1]
            if not supertrend[i] and upperband[i] > upperband[i - 1]:
                upperband[i] = upperband[i - 1]

    return pd.Series(supertrend, index=df.index)


# Additional helpers retained for compatibility

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
    return talib.ATR(data['high'], data['low'], data['close'], timeperiod=period)


def calculate_multi_rsi(data: pd.Series, periods: list) -> dict:
    rsi_dict = {}
    for period in periods:
        rsi_dict[f"rsi_{period}"] = calculate_rsi(data, period)
    return rsi_dict
