import json
import os
from datetime import datetime, timedelta

COOLDOWN_FILE = "logs/strategy_cooldowns.json"
COOLDOWN_HOURS = 4  # adjustable


def set_strategy_cooldown(strategy_name: str, symbol: str, timeframe: str) -> None:
    data = {}
    if os.path.exists(COOLDOWN_FILE):
        with open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}

    key = f"{strategy_name}_{symbol}_{timeframe}"
    data[key] = datetime.utcnow().isoformat()

    os.makedirs(os.path.dirname(COOLDOWN_FILE), exist_ok=True)
    with open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def is_strategy_on_cooldown(strategy_name: str, symbol: str, timeframe: str) -> bool:
    if not os.path.exists(COOLDOWN_FILE):
        return False

    with open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return False

    key = f"{strategy_name}_{symbol}_{timeframe}"
    last_used = data.get(key)

    if not last_used:
        return False

    last_dt = datetime.fromisoformat(last_used)
    return datetime.utcnow() < last_dt + timedelta(hours=COOLDOWN_HOURS)