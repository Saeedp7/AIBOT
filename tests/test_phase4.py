# tests/test_phase4.py

import os
import json
import pytest

LOG_PATH = "logs/trade_log.txt"

def test_log_contains_confidence_lines():
    """Check that confidence logging exists in the trade log."""
    if not os.path.exists(LOG_PATH):
        pytest.skip("No trade_log.txt found")

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Confidence" in content or "Skipping trade" in content, "❌ No confidence logs found."

def test_trade_journal_exists():
    """Ensure the trade history file exists and contains at least one entry."""
    hist_path = "logs/trade_history.json"
    assert os.path.exists(hist_path), "❌ Missing trade_history.json"

    with open(hist_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, list), "❌ trade_history.json is not a list"
        assert len(data) > 0, "❌ No trades found in trade_history.json"
