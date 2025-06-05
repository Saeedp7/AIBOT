import pandas as pd
from ai_engine.context_profiler import detect_support_resistance_levels, is_price_near_level

def compute_confidence(strategy_score: float,
                       regime_compatible: bool,
                       sentiment: int,
                       price: float,
                       market_data: pd.DataFrame,
                       weights: dict = None) -> float:
    """
    Compute confidence score for a trade opportunity.
    Returns a value from 0.0 to 1.0
    """
    if weights is None:
        weights = {
            "strategy_score": 0.4,
            "regime_match": 0.2,
            "sentiment": 0.2,
            "structure": 0.2
        }

    # Normalize strategy score to [0,1] assuming max is 1.0
    strat_score = min(strategy_score, 1.0)

    regime_score = 1.0 if regime_compatible else 0.0
    sentiment_score = {1: 1.0, 0: 0.5, -1: 0.0}.get(sentiment, 0.5)

    support, resistance = detect_support_resistance_levels(market_data)
    structure_score = 0.0 if is_price_near_level(price, support + resistance) else 1.0

    confidence = (
        strat_score * weights["strategy_score"] +
        regime_score * weights["regime_match"] +
        sentiment_score * weights["sentiment"] +
        structure_score * weights["structure"]
    )

    return round(confidence, 3)
