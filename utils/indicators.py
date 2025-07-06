"""Lightweight technical indicator helpers.

This module primarily relies on ``pandas_ta`` for indicator calculations.  The
package may fail to import in minimal environments (for example due to an
incompatible ``numpy`` release).  In that case, a very small pandas/numpy
fallback implementation is used so basic tests and backtests can still run
without the dependency.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

try:  # pragma: no cover - optional dependency
    import pandas_ta as ta  # type: ignore
except Exception:  # pragma: no cover - allow tests without the library
    ta = None


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential moving average."""
    if ta and hasattr(ta, "ema"):
        try:
            result = ta.ema(series, length=period)
            if isinstance(result, pd.DataFrame):
                result = result.iloc[:, 0]
            return result
        except Exception:
            pass
    return series.ewm(span=period, adjust=False).mean()


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    if ta and hasattr(ta, "sma"):
        try:
            result = ta.sma(series, length=period)
            if isinstance(result, pd.DataFrame):
                result = result.iloc[:, 0]
            return result
        except Exception:
            pass
    return series.rolling(window=period).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    if ta and hasattr(ta, "rsi"):
        try:
            result = ta.rsi(series, length=period)
            if isinstance(result, pd.DataFrame):
                result = result.iloc[:, 0]
            return result
        except Exception:
            pass
    diff = series.diff()
    gain = diff.clip(lower=0)
    loss = -diff.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)
    return rsi.fillna(0)


def calculate_macd(
    series: pd.Series,
    fastperiod: int = 12,
    slowperiod: int = 26,
    signalperiod: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return MACD line, signal line and histogram."""
    if ta and hasattr(ta, "macd"):
        try:
            df = ta.macd(series, fast=fastperiod, slow=slowperiod, signal=signalperiod)
            if isinstance(df, pd.DataFrame):
                macd_line = df.iloc[:, 0]
                hist = df.iloc[:, 1]
                signal = df.iloc[:, 2]
                return macd_line, signal, hist
        except Exception:
            pass

    ema_fast = calculate_ema(series, fastperiod)
    ema_slow = calculate_ema(series, slowperiod)
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signalperiod, adjust=False).mean()
    hist = macd - signal
    return macd, signal, hist


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    if ta and hasattr(ta, "vwap"):
        try:
            result = ta.vwap(
                high=df["high"],
                low=df["low"],
                close=df["close"],
                volume=df["volume"],
            )
            if isinstance(result, pd.DataFrame):
                result = result.iloc[:, 0]
            return result
        except Exception:
            pass
    typical = (df["high"] + df["low"] + df["close"]) / 3
    return (typical * df["volume"]).cumsum() / df["volume"].cumsum()


def calculate_bollinger_bands(
    series: pd.Series, period: int = 20, dev: float = 2
) -> tuple[pd.Series, pd.Series, pd.Series]:
    if ta and hasattr(ta, "bbands"):
        try:
            df = ta.bbands(series, length=period, std=dev)
            if isinstance(df, pd.DataFrame) and len(df.columns) >= 3:
                lower = df.iloc[:, 0]
                middle = df.iloc[:, 1]
                upper = df.iloc[:, 2]
                return upper, middle, lower
        except Exception:
            pass

    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma + dev * std
    lower = sma - dev * std
    return upper, sma, lower


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    if ta and hasattr(ta, "adx"):
        try:
            adx_df = ta.adx(df["high"], df["low"], df["close"], length=period)
            if isinstance(adx_df, pd.DataFrame):
                return adx_df.iloc[:, 0]
        except Exception:
            pass

    high_diff = df["high"].diff()
    low_diff = df["low"].diff()
    plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0.0)
    minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0.0)
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift()).abs()
    tr3 = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * pd.Series(plus_dm).rolling(window=period).sum() / atr
    minus_di = 100 * pd.Series(minus_dm).rolling(window=period).sum() / atr
    adx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
    return adx.fillna(0)


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3) -> pd.Series:
    hl2 = (df["high"] + df["low"]) / 2
    if ta and hasattr(ta, "supertrend"):
        try:
            st_df = ta.supertrend(
                df["high"], df["low"], df["close"], length=period, multiplier=multiplier
            )
            if isinstance(st_df, pd.DataFrame):
                direction = st_df.iloc[:, -1]
                return direction
        except Exception:
            pass

    if ta and hasattr(ta, "atr"):
        try:
            atr = ta.atr(df["high"], df["low"], df["close"], length=period)
            if isinstance(atr, pd.DataFrame):
                atr = atr.iloc[:, 0]
        except Exception:
            atr = None
    else:
        atr = None
    if atr is None:
        tr1 = df["high"] - df["low"]
        tr2 = (df["high"] - df["close"].shift()).abs()
        tr3 = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

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

    direction = pd.Series(supertrend, index=df.index).apply(lambda x: 1 if x else -1)
    return direction


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
    if ta and hasattr(ta, "atr"):
        try:
            atr = ta.atr(data["high"], data["low"], data["close"], length=period)
            if isinstance(atr, pd.DataFrame):
                atr = atr.iloc[:, 0]
            return atr
        except Exception:
            pass

    tr1 = data["high"] - data["low"]
    tr2 = (data["high"] - data["close"].shift()).abs()
    tr3 = (data["low"] - data["close"].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_multi_rsi(data: pd.Series, periods: list) -> dict:
    rsi_dict = {}
    for period in periods:
        rsi_dict[f"rsi_{period}"] = calculate_rsi(data, period)
    return rsi_dict
