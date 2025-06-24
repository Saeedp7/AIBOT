import os
import pandas as pd
from data.chart_data_handler import get_ohlcv
from risk_management.stop_loss_manager import get_required_timeframes
from ai_engine.score_updater import get_strategy_win_rate, load_scores
import numpy as np

from strategies import discover_strategies
from ai_engine.score_manager import ensure_base_scores


class StrategySelector:
    def __init__(self):
        self.strategies = discover_strategies()
        ensure_base_scores(
            [s.__class__.__name__ for s in self.strategies]
        )
        self.cooldowns = {}
        self.strategy_memory = load_scores()

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