import numpy as np
import json
import os
from collections import defaultdict
from risk_management.stop_loss_manager import determine_sl_tp

class StrategyChooser:
    def __init__(self, memory_file="ai_engine/ai_memory.json"):
        self.performance_log = {}
        self.memory_file = memory_file
        self.load_memory()

    def analyze_market(self, data):
        volatility = np.std(data['close'].pct_change().dropna()) * 100
        trend_strength = abs(data['close'].iloc[-1] - data['close'].iloc[-20]) / data['close'].iloc[-20]
        if trend_strength > 0.015:
            return 'trending'
        elif volatility > 1.5:
            return 'volatile'
        else:
            return 'ranging'

    def choose_best_strategy(self, strategies: list, multi_tf_data: dict):
        regime_data = multi_tf_data.get("M15")
        if regime_data is None or regime_data.empty:
            # Fallback to first non-empty timeframe
            regime_data = next((df for df in multi_tf_data.values() if not df.empty), None)
            if regime_data is None:
                raise ValueError("All timeframe dataframes are empty.")
        regime = self.analyze_market(regime_data)
        print(f"[AI Engine] Market regime: {regime}")

        ranked = []
        for strat in strategies:
            tf = getattr(strat, "preferred_tf", "M15")
            tf_data = multi_tf_data.get(tf)
            if tf_data is None or tf_data.empty:
                continue
            try:
                strat.analyze(tf_data)
                group = getattr(strat, "strategy_group", "day")
                confidence = self._score_strategy_fit(strat, regime, group)
                ranked.append((strat, confidence))
            except Exception as e:
                print(f"⚠️ {strat.__class__.__name__} failed: {e}")

        if not ranked:
            print("⚠️ No strategy passed evaluation.")
            return None

        best_strategy = max(ranked, key=lambda x: x[1])[0]
        return best_strategy

    def determine_sl_tp(self, strategy_name, entry_price, direction, market_data, symbol=""):
        return determine_sl_tp(
            strategy_name, entry_price, direction, market_data, symbol=symbol
        )

    def _score_strategy_fit(self, strat, regime, group):
        weights = {
            'scalping': {'volatile': 0.8, 'trending': 0.4, 'ranging': 0.6},
            'day': {'volatile': 0.7, 'trending': 0.8, 'ranging': 0.6},
            'swing': {'volatile': 0.3, 'trending': 0.9, 'ranging': 0.5},
        }
        strategy_name = strat.__class__.__name__
        weight = weights.get(group, {}).get(regime, 0.5)
        performance = self.performance_log.get(strategy_name, {"win_rate": 0.5})
        base = performance["win_rate"]
        return weight * base

    def score_strategy(self, strategy_name: str, result: dict):
        stats = self.performance_log.get(strategy_name, {"win_rate": 0.5, "count": 0, "avg_drawdown": 0.0})
        count = stats["count"] + 1
        win_rate = (stats["win_rate"] * stats["count"] + int(result['win'])) / count
        avg_drawdown = (stats["avg_drawdown"] * stats["count"] + result.get("drawdown", 0.0)) / count
        self.performance_log[strategy_name] = {"win_rate": win_rate, "count": count, "avg_drawdown": avg_drawdown}
        self.save_memory()

    def save_memory(self):
        try:
            os.makedirs("ai_engine", exist_ok=True)
            with open(self.memory_file, "w") as f:
                json.dump(self.performance_log, f, indent=2)
        except Exception as e:
            print(f"❌ Failed to save AI memory: {e}")

    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    self.performance_log = json.load(f)
                print("✅ AI memory loaded.")
            except Exception as e:
                print(f"❌ Failed to load AI memory: {e}")
        else:
            print("🧠 No prior AI memory found. Starting fresh.")
