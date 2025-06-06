# indicators/indicator_engine.py

"""Compute technical indicators for OHLCV dataframes."""

from __future__ import annotations

from typing import Dict

import pandas as pd
import pandas_ta as ta

from utils.indicators import (
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_vwap,
)


def add_indicators(data_dict: Dict[str, Dict[str, pd.DataFrame]]) -> Dict[str, Dict[str, pd.DataFrame]]:
    """Append common technical indicators to each DataFrame in ``data_dict``.

    Parameters
    ----------
    data_dict : dict
        Nested ``{symbol: {timeframe: DataFrame}}`` structure as returned by
        :func:`preprocess_ohlcv_data`.

    Returns
    -------
    dict
        Same structure with additional indicator columns added.
    """
    for symbol, frames in data_dict.items():
        for tf, df in frames.items():
            df = df.copy()

            # Moving averages
            df["ema_14"] = calculate_ema(df["close"], 14)
            df["ema_50"] = calculate_ema(df["close"], 50)

            # RSI
            df["rsi_14"] = calculate_rsi(df["close"], 14)

            # MACD components
            macd_line, signal_line, hist = calculate_macd(df["close"], 12, 26, 9)
            df["macd"] = macd_line
            df["macd_signal"] = signal_line
            df["macd_hist"] = hist

            # VWAP
            df["vwap"] = calculate_vwap(df)

            # Ichimoku cloud
            conv_base, cloud = ta.ichimoku(
                high=df["high"], low=df["low"], close=df["close"], offset=0
            )
            if conv_base is not None:
                if "ITS_9" in conv_base.columns:
                    df["tenkan_sen"] = conv_base["ITS_9"]
                if "KJS_26" in conv_base.columns:
                    df["kijun_sen"] = conv_base["KJS_26"]
            if cloud is not None:
                if "SSA_9_26_52" in cloud.columns:
                    df["senkou_span_a"] = cloud["SSA_9_26_52"]
                if "SSB_9_26_52" in cloud.columns:
                    df["senkou_span_b"] = cloud["SSB_9_26_52"]

            frames[tf] = df

    return data_dict