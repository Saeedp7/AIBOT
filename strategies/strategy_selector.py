import os
import pandas as pd
from data.chart_data_handler import get_ohlcv
from risk_management.stop_loss_manager import get_required_timeframes
from ai_engine.score_updater import (
    get_strategy_win_rate,
    load_scores,
    calculate_composite_score,
)
from config.thresholds import get_confidence_threshold


def get_current_regime() -> str:
    """Return most recently detected market regime if available."""
    path = "logs/current_regime.txt"
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                value = f.read().strip()
                if value:
                    return value
        except Exception:
            pass
    return "unknown"


def get_strategy_score(strategy_name: str, regime: str) -> float:
    """Return composite score for ``strategy_name`` in ``regime``."""
    scores = load_scores()
    data = scores.get(strategy_name, {})
    metrics = {}
    if isinstance(data, dict):
        if regime in data and isinstance(data[regime], dict):
            metrics = data[regime]
        elif "unknown" in data and isinstance(data["unknown"], dict):
            metrics = data["unknown"]
        elif all(k in data for k in ("win_rate", "recent_score", "regime_fit")):
            metrics = data
    return calculate_composite_score(metrics) if metrics else 0.0
import numpy as np

from strategies import discover_strategies
from ai_engine.score_manager import ensure_base_scores


class StrategySelector:
    def __init__(self):
        all_strategies = discover_strategies()
        print(
            "[StrategySelector] All loaded strategies:",
            [s.__class__.__name__ for s in all_strategies],
        )
        ensure_base_scores([s.__class__.__name__ for s in all_strategies])

        self.active_strategies = self._filter_by_regime_and_score(all_strategies)
        self.strategies = list(self.active_strategies)
        print(
            "[StrategySelector] Active strategies selected:",
            [s.__class__.__name__ for s in self.active_strategies],
        )

        self.cooldowns = {}
        self.strategy_memory = load_scores()

    def _filter_by_regime_and_score(self, strategies):
        filtered = []
        for strat in strategies:
            try:
                regime = get_current_regime()
                name = strat.__class__.__name__
                threshold = get_confidence_threshold(symbol="XAUUSD", timeframe="M15", regime=regime, strategy_name=name)
                score = get_strategy_score(name, regime)

                if score >= threshold:
                    filtered.append(strat)
                else:
                    print(f"[Filter] Strategy {name} skipped due to score ({score} < {threshold})")
            except Exception as e:
                print(f"[Filter] Strategy {name} error: {e}")

        return filtered

    def fetch_multitimeframe_data(self, timeframes):
        tf_data = {}
        for tf in timeframes:
            try:
                data = get_ohlcv(timeframe=tf)
                if data is not None and not data.empty:
                    tf_data[tf] = data
                else:
                    print(f"⚠️ No data for timeframe {tf}")
            except Exception as e:
                print(f"❌ Error fetching data for timeframe {tf}: {e}")
        return tf_data

    def get_market_regime(self, df, *, symbol: str | None = None):
        from ai_engine.regime_classifier import detect_market_regime

        return detect_market_regime(df, symbol=symbol)

    def select_strategy(self, multi_tf_data):
        best_score = -1
        selected_strategy = None
        tf = list(multi_tf_data.keys())[0]
        df = multi_tf_data[tf].copy()
        regime = self.get_market_regime(df)
        print(f"🌐 Market Regime Detected: {regime}")

        for strategy in self.strategies:
            name = strategy.__class__.__name__

            if name in self.cooldowns and self.cooldowns[name] > 0:
                print(f"⏳ {name} on cooldown, skipping...")
                self.cooldowns[name] -= 1
                continue

            group = getattr(strategy, "strategy_group", "day").lower()
            if regime == 'volatile' and group == 'swing':
                print(f"⚠️ Skipping {name} due to volatile regime and swing strategy.")
                continue

            try:
                strategy.analyze(df)
                signal = strategy.signal
                print(f"🔍 {name}: signal = {signal}")

                if signal in ['buy', 'sell']:
                    base_score = self.score_strategy(df, signal)
                    win_rate_boost = get_strategy_win_rate(name) / 100
                    adjusted_score = round(base_score + win_rate_boost, 2)
                    print(f"📈 {name} score = {adjusted_score} (base: {base_score}, win-rate: {round(win_rate_boost, 2)})")

                    if adjusted_score > best_score:
                        best_score = adjusted_score
                        selected_strategy = strategy

            except Exception as e:
                print(f"❌ Strategy {name} failed: {e}")

        return selected_strategy

    def get_all_strategies(self):
        return self.strategies

    def score_strategy(self, df, signal):
        if len(df) < 10:
            return 0
        close = df['close']
        volatility = (close.max() - close.min()) / close.mean()
        trend = close.iloc[-1] - close.iloc[-10]
        score = 0
        if signal == 'buy' and trend > 0:
            score += 1
        elif signal == 'sell' and trend < 0:
            score += 1
        score += min(volatility * 10, 1.0)
        return round(score, 2)

    def set_strategy_cooldown(self, strategy_name, bars=10):
        self.cooldowns[strategy_name] = bars

    def check_all(
        self,
        symbol: str,
        timeframe: str,
        df,
        regime: str,
    ) -> dict[str, str | None]:
        """Run check_signal for each strategy and return signal results."""
        results = {}
        for strat in self.strategies:
            name = strat.__class__.__name__
            try:
                results[name] = strat.check_signal(symbol, timeframe, df, regime)
            except Exception as e:
                print(f"⚠️ {name} failed: {e}")
                results[name] = None
        return results