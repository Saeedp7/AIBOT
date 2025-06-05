# execution/order_manager.py

import time
import os

# Path to trade log
TRADE_LOG_PATH = "logs/trade_log.txt"

def log_trade(action, symbol, lot_size, price, sl=None, tp=None):
    """Log a trade to the trade log file."""
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {action.upper()} {lot_size} {symbol} at {price:.2f} SL: {sl} TP: {tp}\n"
    
    with open(TRADE_LOG_PATH, "a") as file:
        file.write(log_entry)

    print(f"📝 {log_entry.strip()}")

def execute_fake_order(action, symbol, lot_size, price, sl=None, tp=None):
    """Simulate order execution (no real trade)."""
    print(f"🔔 {action.upper()} {lot_size} {symbol} at {price:.2f} (Simulated)")
    log_trade(action, symbol, lot_size, price, sl, tp)
