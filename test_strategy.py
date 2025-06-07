# test_env_config.py
import os
from config.manager import get_config

def test_env_loading():
    print("🔧 Testing .env loading via get_config()...")

    test_keys = [
        "MT5_LOGIN",
        "MT5_PASSWORD",
        "MT5_SERVER",
        "LIVE_MODE",
        "SYMBOLS",
        "TIMEFRAMES",
        "TELEGRAM_BOT_TOKEN",
        "DISCORD_WEBHOOK_URL"
    ]

    for key in test_keys:
        val = get_config(key)
        print(f"✅ {key} = {val if val else '⚠️ Not Set'}")

if __name__ == "__main__":
    test_env_loading()
