import pandas as pd

def is_higher_highs_last_n(df: pd.DataFrame, n: int = 3) -> bool:
    """Return True if the last n highs are consecutively higher."""
    highs = df["high"].tail(n).values
    return all(earlier < later for earlier, later in zip(highs, highs[1:]))


def is_lower_lows_last_n(df: pd.DataFrame, n: int = 3) -> bool:
    """Return True if the last n lows are consecutively lower."""
    lows = df["low"].tail(n).values
    return all(earlier > later for earlier, later in zip(lows, lows[1:]))


def is_higher_lows_last_n(df: pd.DataFrame, n: int = 3) -> bool:
    """Return True if the last n lows form higher lows."""
    lows = df["low"].tail(n).values
    return all(earlier < later for earlier, later in zip(lows, lows[1:]))


def is_lower_highs_last_n(df: pd.DataFrame, n: int = 3) -> bool:
    """Return True if the last n highs form lower highs."""
    highs = df["high"].tail(n).values
    return all(earlier > later for earlier, later in zip(highs, highs[1:]))