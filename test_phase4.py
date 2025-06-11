# test_phase4.py
import unittest
import os
import json
from typing import Dict, Any

class TestPhase4(unittest.TestCase):

    def setUp(self):
        self.history_path = "logs/trade_history.json"
        self.score_path = "ai_engine/strategy_scores.json"
        self.log_path = "logs/trade_log.txt"
        self.report_path = "logs/performance_report.json"

    def test_trade_history_fields(self):
        """Ensure all closed trades include key analysis fields."""
        self.assertTrue(os.path.exists(self.history_path), "❌ trade_history.json is missing.")
        with open(self.history_path, "r", encoding="utf-8") as f:
            trades = json.load(f)

        closed_trades = [t for t in trades if t.get("result") not in (None, "open")]
        self.assertGreater(len(closed_trades), 0, "❌ No closed trades found.")
        for trade in closed_trades:
            for key in ["exit", "close_time", "profit_pct", "regime"]:
                self.assertIn(key, trade, f"❌ Missing field '{key}' in trade: {trade}")

    def test_strategy_score_structure(self):
        """Check regime-level strategy metrics are properly nested."""
        self.assertTrue(os.path.exists(self.score_path), "❌ strategy_scores.json missing.")
        with open(self.score_path, "r", encoding="utf-8") as f:
            scores: Dict[str, Any] = json.load(f)

        for strategy, regimes in scores.items():
            if not isinstance(regimes, dict):
                continue  # skip if flat
            for regime, metrics in regimes.items():
                if not isinstance(metrics, dict):
                    continue  # skip flat fields
                for key in ["win_rate", "recent_score", "regime_fit"]:
                    self.assertIn(key, metrics, f"❌ Missing '{key}' in {strategy}/{regime}")

    def test_confidence_logging_present(self):
        """Verify that confidence scoring logs exist and are used."""
        self.assertTrue(os.path.exists(self.log_path), "❌ trade_log.txt missing.")
        with open(self.log_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Confidence", content, "❌ Confidence values not logged.")
        self.assertIn("Skipping trade", content, "❌ No skipped trades due to low confidence.")

    def test_performance_report_fields(self):
        """Ensure strategy report contains expected statistics."""
        self.assertTrue(os.path.exists(self.report_path), "❌ performance_report.json not found.")
        with open(self.report_path, "r", encoding="utf-8") as f:
            stats = json.load(f)

        self.assertGreater(len(stats), 0, "❌ Report contains no data.")
        for strategy, values in stats.items():
            for field in ["trades", "win_rate", "avg_pnl", "avg_regime_score"]:
                self.assertIn(field, values, f"❌ Missing '{field}' in {strategy} stats.")


if __name__ == "__main__":
    unittest.main()
