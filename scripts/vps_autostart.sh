#!/bin/bash
# Launch the live bot on VPS reboot

DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"

if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

python scripts/deploy_runner.py &