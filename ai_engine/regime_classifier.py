import pandas as pd

def detect_market_regime(df: pd.DataFrame, window: int = 20, slope_threshold: float = 0.01, volatility_threshold: float = 0.015):
    """
    Enhanced regime classifier based on rolling volatility and price slope.
    Returns: 'trending', 'volatile', or 'ranging'
    """
    if len(df) < window:
        return "unknown"

    recent = df['close'].iloc[-window:]
    returns = recent.pct_change().dropna()
    volatility = returns.std()
    slope = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0]

    if abs(slope) > slope_threshold:
        return "trending"
    elif volatility > volatility_threshold:
        return "volatile"
    else:
        return "ranging"
