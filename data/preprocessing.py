"""Data preprocessing utilities for OHLCV datasets."""

from __future__ import annotations

from typing import Dict

import pandas as pd


def preprocess_ohlcv_data(
    data: Dict[str, Dict[str, pd.DataFrame]]
) -> Dict[str, Dict[str, pd.DataFrame]]:
    """Clean and standardize OHLCV datasets.

    Parameters
    ----------
    data : dict
        Nested ``{symbol: {timeframe: DataFrame}}`` structure produced by
        :func:`collect_ohlcv_data`.

    Returns
    -------
    dict
        The same structure with cleaned ``DataFrame`` objects.
    """
    for symbol, frames in data.items():
        for tf, df in frames.items():
            df = df.copy()

            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index, errors="coerce")

            # Make timezone-aware (UTC)
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
            else:
                df.index = df.index.tz_convert("UTC")

            # Drop duplicate timestamps and sort
            df = df[~df.index.duplicated(keep="first")]
            df = df.sort_index()

            # Forward fill missing values
            df = df.ffill()

            frames[tf] = df

    return data