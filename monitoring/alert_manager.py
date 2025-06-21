import requests
import time
from collections import deque
from datetime import datetime
from config.manager import get_config

TELEGRAM_BOT_TOKEN = get_config("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = get_config("TELEGRAM_CHAT_ID", "")

telegram_queue: deque[dict] = deque()
MAX_RETRIES = 3

def _send_telegram(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception:
        return False


def _notify(message: str) -> None:
    if not _send_telegram(message):
        telegram_queue.append({"msg": message, "retries": 0, "ts": datetime.utcnow()})


def retry_failed_alerts() -> None:
    for alert in list(telegram_queue):
        if alert["retries"] >= MAX_RETRIES:
            print(f"⚠️ Telegram failed for: {alert['msg']}")
            telegram_queue.remove(alert)
            continue
        if _send_telegram(alert["msg"]):
            telegram_queue.remove(alert)
        else:
            alert["retries"] += 1
            time.sleep(2 ** alert["retries"])


def alert_trade_opened(symbol: str, timeframe: str, direction: str, entry: float, sl: float, tp: float) -> None:
    msg = (
        f"📈 Trade opened {symbol} {timeframe} {direction.upper()}\n"
        f"Entry: {entry} SL: {sl} TP: {tp}"
    )
    _notify(msg)


def alert_sl_moved(symbol: str, timeframe: str, new_sl: float) -> None:
    msg = f"🔔 SL moved for {symbol} {timeframe} -> {new_sl}"
    _notify(msg)


def alert_trade_closed(symbol: str, timeframe: str, reason: str) -> None:
    msg = f"✅ Trade closed {symbol} {timeframe} ({reason})"
    _notify(msg)


def alert_daily_guard(reason: str) -> None:
    msg = f"🚫 Daily guard triggered: {reason}"
    _notify(msg)