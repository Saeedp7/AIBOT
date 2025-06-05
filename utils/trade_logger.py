# utils/trade_logger.py

import csv
import os
from datetime import datetime

LOG_FILE = "trade_logs.csv"

def log_trade(symbol, direction, entry_price, exit_price, volume, strategy, result, pnl, regime):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Time", "Symbol", "Strategy", "Direction", "Entry", "Exit", "Volume", "Result", "PnL", "Regime"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol,
            strategy,
            direction,
            round(entry_price, 2),
            round(exit_price, 2),
            volume,
            result,
            round(pnl, 2),
            regime
        ])
