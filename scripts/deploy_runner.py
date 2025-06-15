#!/usr/bin/env python
"""Production launcher for AutoTrade AI Bot."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

PID_FILE = LOG_DIR / "deploy_runner.pid"

# Prevent multiple instances
if PID_FILE.exists():
    try:
        old_pid = int(PID_FILE.read_text().strip())
        os.kill(old_pid, 0)
    except Exception:
        PID_FILE.unlink(missing_ok=True)
    else:
        print("Deploy runner already running. Exiting.")
        sys.exit(0)

PID_FILE.write_text(str(os.getpid()))

log_path = LOG_DIR / "live_session.log"
if log_path.exists():
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_path.rename(LOG_DIR / f"live_session_{timestamp}.log")

cmd = [sys.executable, str(ROOT / "run_bot.py"), "--live", "--debug"]
with open(log_path, "a", encoding="utf-8") as f:
    subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)

PID_FILE.unlink(missing_ok=True)