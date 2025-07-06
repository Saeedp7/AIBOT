import json
import os

THRESHOLD_FILE = "config/strategy_thresholds.json"

DEFAULT_CONFIDENCE_THRESHOLDS = {
    "bull": 0.3,
    "bear": 0.3,
    "volatile": 0.3,
}

def load_strategy_thresholds():
    if os.path.exists(THRESHOLD_FILE):
        with open(THRESHOLD_FILE, "r") as f:
            return json.load(f)
    return {}


def get_confidence_threshold(symbol: str, timeframe: str, regime: str, strategy_name: str) -> float:
    overrides = load_strategy_thresholds()
    if strategy_name in overrides:
        try:
            return float(overrides[strategy_name])
        except (TypeError, ValueError):
            pass
    return float(DEFAULT_CONFIDENCE_THRESHOLDS.get(regime, 0.3))