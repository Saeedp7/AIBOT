import pandas as pd
from datetime import datetime
from ai_engine.score_updater import load_scores
from ai_engine.sentiment_analyzer import fetch_forex_factory_news, analyze_sentiment
from ai_engine.context_profiler import detect_support_resistance_levels, is_price_near_level
from ai_engine.parameter_optimizer import log_trade_decision, suggest_thresholds, load_strategy_thresholds
from ai_engine.strategy_config import STRATEGY_SR_SENSITIVITY

# Load once per run
news_items = fetch_forex_factory_news()
sentiment_data = analyze_sentiment(news_items)
strategy_thresholds = load_strategy_thresholds()

def get_strategy_group(strategy_name):
    if "Swing" in strategy_name:
        return "swing"
    elif "Scalping" in strategy_name or "Breakout" in strategy_name:
        return "scalp"
    else:
        return "day"

def is_regime_compatible(strategy_group, regime):
    if regime == "volatile" and strategy_group == "swing":
        return False
    return True

def should_execute_trade(currency: str, current_time: datetime):
    for item in sentiment_data:
        if item['currency'] == currency and abs((current_time - item['time']).total_seconds()) < 3600:
            if item['sentiment'] < 0:
                return False
    return True

def evaluate_signals(strategy_signals: dict, market_regime: str,
                     currency: str = "USD", market_data: pd.DataFrame = None, symbol: str = "XAUUSD"):

    strategy_scores = load_scores()
    price = market_data['close'].iloc[-1]
    support, resistance = detect_support_resistance_levels(market_data)

    print(f"🧱 Support levels: {support}")
    print(f"🧱 Resistance levels: {resistance}")
    print(f"📍 Current price: {price}")

    candidates = []

    for strat_name, signal in strategy_signals.items():
        raw_score = strategy_scores.get(strat_name, 0.7)
        if isinstance(raw_score, dict):
            score = raw_score.get(market_regime, 0.0)
        else:
            score = float(raw_score)
        group = get_strategy_group(strat_name)
        raw_thresh = strategy_thresholds.get(strat_name, 0.0)
        if isinstance(raw_thresh, dict):
            threshold = raw_thresh.get(market_regime, 0.0)
        else:
            threshold = float(raw_thresh)

        sr_sensitivity = STRATEGY_SR_SENSITIVITY.get(strat_name, "high")
        near_sr = is_price_near_level(price, support + resistance, symbol, sr_sensitivity)

        if signal not in ["buy", "sell"]:
            continue
        if score < threshold:
            continue
        if not is_regime_compatible(group, market_regime):
            continue

        # Handle S/R logic
        if sr_sensitivity == "high" and near_sr:
            print(f"📛 Skipped {strat_name} → too close to S/R (high sensitivity)")
            continue
        elif sr_sensitivity == "low" and near_sr:
            print(f"⚠️ Caution: {strat_name} near S/R — still considering (low sensitivity)")
        elif sr_sensitivity == "none":
            pass  # ignore S/R

        candidates.append((strat_name, signal, score))

    current_time = datetime.utcnow()
    candidates = [c for c in candidates if should_execute_trade(currency, current_time)]

    if not candidates:
        log_trade_decision(reason="no_valid_candidates", strategy=None, outcome="skip")
        return "hold", None

    candidates.sort(key=lambda x: x[2], reverse=True)
    top_strategy, top_signal, top_score = candidates[0]

    log_trade_decision(reason="selected", strategy=top_strategy, outcome=top_signal)
    suggest_thresholds()

    return top_signal, top_strategy
