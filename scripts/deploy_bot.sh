#!/bin/bash

# Activate virtual environment and launch scheduler with auto-restart

DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$DIR/logs/live_output.log"
VENV="$DIR/venv/bin/activate"

if [ ! -f "$VENV" ]; then
  echo "Virtualenv not found: $VENV" >&2
  exit 1
fi

source "$VENV"

while true; do
  echo "[\$(date -u)] Starting scheduler..." >> "$LOG_FILE"
  python -u "$DIR/live/scheduler_loop.py" >> "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  echo "[\$(date -u)] Bot exited with code $EXIT_CODE. Restarting in 5s..." >> "$LOG_FILE"
  sleep 5
done