import json
from datetime import datetime

SUPPRESSED_LOG = "logs/suppressed_strategies.json"


def log_suppressed_strategy(strategy_name: str, score: float, regime: str, threshold: float) -> None:
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "strategy": strategy_name,
        "regime": regime,
        "score": score,
        "threshold": threshold,
    }

    data = []
    try:
        with open(SUPPRESSED_LOG, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass

    data.append(entry)

    with open(SUPPRESSED_LOG, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)