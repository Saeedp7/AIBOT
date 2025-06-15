# 🚀 Deployment & VPS Guide

This document explains how to run AutoTrade AI Bot in production.

## ✅ System Requirements

- Ubuntu 20.04+ (or Windows Server with Python 3.10+)
- MetaTrader 5 installed and running
- Python virtual environment with required packages

## 🛠️ Environment Setup

Create a `.env` file in the project root:

```dotenv
LIVE_MODE=true
MT5_LOGIN=123456
MT5_PASSWORD=your_password
MT5_SERVER=YourBroker-Server
```

Adjust other variables in `config/settings.json` as needed.

## 🔑 MT5 Login

Ensure the MT5 terminal is logged in with the credentials above. The bot
connects via the MetaTrader5 Python API and uses these settings from the
environment.

## ▶️ Running Manually

Activate the venv and start the bot with debug logs:

```bash
source venv/bin/activate
python run_bot.py --live --debug
```

## 🏃 Background Execution

Use a terminal multiplexer or simple background command:

- `screen` or `tmux`
- `nohup python scripts/deploy_runner.py &`

Logs are written to `logs/live_session.log` and rotated on each launch.

## 🔄 VPS Autostart

Copy `scripts/vps_autostart.sh` to your server and add to crontab:

```bash
crontab -e
# Run on reboot
@reboot /path/to/project/scripts/vps_autostart.sh
```

Alternatively create a systemd service pointing to the same script.

## ♻️ Restart Logic

`deploy_runner.py` rotates logs and prevents multiple instances using a pidfile.
If the process exits it can be relaunched manually or via the cron/service.

Check logs under `logs/` for troubleshooting connection errors or crashes.