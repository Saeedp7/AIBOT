import json
import os
from collections import defaultdict
from datetime import datetime

LOG_FILE = "decision_log.json"
THRESHOLD_FILE = "strategy_thresholds.json"


def log_trade_decision(reason: str, strategy: str = None, outcome: str = "hold"):
    """Log each AI decision for review and adaptive learning."""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "reason": reason,
        "strategy": strategy,
        "outcome": outcome
    }

    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []

    logs.append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


def suggest_thresholds():
    """Analyze logs and suggest optimal threshold tuning."""
    if not os.path.exists(LOG_FILE):
        print("📭 No logs found for threshold optimization.")
        return

    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load decision logs: {e}")
        return

    stats = defaultdict(lambda: {"buy": 0, "sell": 0, "skip": 0})

    for entry in logs:
        strat = entry.get("strategy", "unknown")
        outcome = entry.get("outcome", "hold")
        stats[strat][outcome] += 1

    print("📊 Strategy Decision Stats:")
    new_thresholds = {}
    for strat, result in stats.items():
        total = sum(result.values())
        if total == 0:
            continue
        buy_pct = (result["buy"] / total) * 100
        sell_pct = (result["sell"] / total) * 100
        skip_pct = (result["skip"] / total) * 100
        print(f" - {strat}: Buy {buy_pct:.1f}%, Sell {sell_pct:.1f}%, Skip {skip_pct:.1f}%")

        if buy_pct + sell_pct > 60:
            new_thresholds[strat] = round(min(1.0, 0.2 + (buy_pct / 100)), 2)
        else:
            new_thresholds[strat] = 0.0

    with open(THRESHOLD_FILE, "w") as f:
        json.dump(new_thresholds, f, indent=2)

    print("🧠 AI updated strategy thresholds based on performance.")


def load_strategy_thresholds():
    if os.path.exists(THRESHOLD_FILE):
        try:
            with open(THRESHOLD_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}
