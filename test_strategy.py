import os
from dotenv import load_dotenv
from monitoring import alert_manager

# Load environment variables from .env file (if available)
load_dotenv()

# Run each alert function as a test
print("🔔 Testing alert_trade_opened...")
alert_manager.alert_trade_opened("XAUUSD", "M15", "buy", entry=2323.5, sl=2318.0, tp=2335.0)

print("🔔 Testing alert_sl_moved...")
alert_manager.alert_sl_moved("XAUUSD", "M15", new_sl=2325.0)

print("🔔 Testing alert_trade_closed...")
alert_manager.alert_trade_closed("XAUUSD", "M15", reason="TP Hit")

print("🔔 Testing alert_daily_guard...")
alert_manager.alert_daily_guard("Max trades per day reached.")
