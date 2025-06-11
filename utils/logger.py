import os
from datetime import datetime
LOG_PATH = "logs/trade_log.txt"

def log_risk_guard(message: str):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "risk_guard.log")
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
      f.write(f"[{timestamp}] {message}\n")

def log_trade_action(message: str):
    log_dir = "logs"
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    log_file = os.path.join(log_dir, "trade_actions.log")
    timestamp = datetime.utcnow().isoformat() + "Z"
    try:
        with open(LOG_PATH, "a", encoding="utf-8", buffering=1) as f:
            f.write(f"[{timestamp}] {message}\n")
            f.flush()  # Ensure buffer is written immediately
    except Exception as e:
        print(f"❌ Failed to write to log file: {e}")
