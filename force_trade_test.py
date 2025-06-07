
import pandas as pd
from risk_management.daily_guard import DailyGuard
from utils.logger import log_trade_action
from datetime import datetime
import json
import os

# Load test data
data_path = "logs/force_trade_test_data.csv"
df = pd.read_csv(data_path)

# Simulated trade decision
entry_price = df["close"].iloc[-1]
symbol = "XAUUSD"
direction = "buy"
volume = 0.01
sl = entry_price - 10
tp = entry_price + 20
pnl = -100  # Simulate a loss

# Initialize and test DailyGuard
guard = DailyGuard(loss_limit_percent=5.0, max_trades=3)
print(f"📊 DailyGuard before trade: Trades={guard.trades}, PnL={guard.pnl}, CanTrade={guard.can_trade()}")

# Record trade result
if guard.can_trade():
    guard.record_trade(pnl)
    log_trade_action("Executed force trade", {
        "symbol": symbol,
        "entry": entry_price,
        "direction": direction,
        "sl": sl,
        "tp": tp,
        "volume": volume,
        "pnl": pnl,
        "time": str(datetime.utcnow())
    })
    print("✅ Force trade executed and logged.")
else:
    print("⛔ DailyGuard blocked the trade due to limits.")

# Show state after trade
print(f"📊 DailyGuard after trade: Trades={guard.trades}, PnL={guard.pnl}, CanTrade={guard.can_trade()}")

# Check logs
if os.path.exists("logs/trade_actions.log"):
    with open("logs/trade_actions.log", "r") as f:
        print("\n📄 trade_actions.log:")
        print(f.read())

if os.path.exists("logs/risk_guard.log"):
    with open("logs/risk_guard.log", "r") as f:
        print("\n📄 risk_guard.log:")
        print(f.read())
