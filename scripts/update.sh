#!/bin/bash

# Update repository and dependencies, then restart deploy script

DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$DIR/logs/live_output.log"
VENV="$DIR/venv/bin/activate"

cd "$DIR"

echo "[\$(date -u)] Pulling latest code..." >> "$LOG_FILE"
if git pull --rebase >> "$LOG_FILE" 2>&1; then
  echo "[\$(date -u)] Installing dependencies..." >> "$LOG_FILE"
  if [ -f "$VENV" ]; then
    source "$VENV"
    pip install -r requirements.txt >> "$LOG_FILE" 2>&1
  fi
fi

# Relaunch the bot using deploy_bot.sh (will not return)
exec "$DIR/scripts/deploy_bot.sh"