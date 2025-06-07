import os
from datetime import datetime

LOG_PATH = "logs/trade_actions.log"

def log_trade_action(message: str) -> None:
    """Append a time-stamped message to ``trade_actions.log``."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
