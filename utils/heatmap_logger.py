import json
import os
from datetime import datetime

HEATMAP_FILE = "logs/strategy_heatmap.json"


def log_strategy_heatmap(strategy_name: str, symbol: str, timeframe: str, regime: str, outcome: str) -> None:
    data = {}
    if os.path.exists(HEATMAP_FILE):
        with open(HEATMAP_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}

    key = f"{symbol}_{timeframe}_{regime}"
    if key not in data:
        data[key] = {}

    if strategy_name not in data[key]:
        data[key][strategy_name] = {"wins": 0, "losses": 0, "last_used": None}

    if outcome == "win":
        data[key][strategy_name]["wins"] += 1
    elif outcome == "loss":
        data[key][strategy_name]["losses"] += 1

    data[key][strategy_name]["last_used"] = datetime.utcnow().isoformat()

    os.makedirs(os.path.dirname(HEATMAP_FILE), exist_ok=True)
    with open(HEATMAP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)