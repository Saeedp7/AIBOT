import os
import pandas as pd
from data.chart_data_handler import get_ohlcv
from risk_management.stop_loss_manager import get_required_timeframes
from ai_engine.strategy_scorer import get_strategy_win_rate, load_strategy_scores
import numpy as np

# Import all 13 strategies
from strategies.ema_crossover_scalping import EMACrossoverScalpingStrategy
from strategies.macd_divergence import MACDDivergenceStrategy
from strategies.ichimoku_day import IchimokuDayStrategy
from strategies.vwap_reversion import VWAPReversionStrategy
from strategies.order_block_scalping import OrderBlockScalpingStrategy
from strategies.micro_breakout_scalping import MicroBreakoutScalpingStrategy
from strategies.trend_pullback import TrendPullbackStrategy
from strategies.supply_demand_swing import SupplyDemandSwingStrategy
from strategies.delta_scalping import DeltaDivergenceScalpingStrategy
from strategies.volume_breakout import VolumeBreakoutStrategy
from strategies.fibonacci_swing import FibonacciSwingStrategy
from strategies.london_breakout import LondonBreakoutStrategy
from strategies.ma_crossover_swing import MACrossoverSwingStrategy
from strategies.supertrend_adx_rsi_strategy import SupertrendADXRSIStrategy
from strategies.breakout_strategy import BreakoutStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.trend_following import TrendFollowingStrategy


class StrategySelector:
    def __init__(self):
        self.strategies = [
            EMACrossoverScalpingStrategy(),
            MACDDivergenceStrategy(),
            IchimokuDayStrategy(),
            VWAPReversionStrategy(),
            OrderBlockScalpingStrategy(),
            MicroBreakoutScalpingStrategy(),
            TrendPullbackStrategy(),
            SupplyDemandSwingStrategy(),
            DeltaDivergenceScalpingStrategy(),
            VolumeBreakoutStrategy(),
            FibonacciSwingStrategy(),
            LondonBreakoutStrategy(),
            MACrossoverSwingStrategy(),
            SupertrendADXRSIStrategy(),
            BreakoutStrategy(),
            MeanReversionStrategy(),
           TrendFollowingStrategy(),
        ]
        self.cooldowns = {}
        self.strategy_memory = load_strategy_scores()

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

    def get_market_regime(self, df):
        volatility = np.std(df['close'].pct_change().dropna()) * 100
        trend_strength = abs(df['close'].iloc[-1] - df['close'].iloc[-20]) / df['close'].iloc[-20]
        if trend_strength > 0.015:
            return 'trending'
        elif volatility > 1.5:
            return 'volatile'
        else:
            return 'ranging'

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

    def check_all(self, df) -> dict[str, str | None]:
     """Run check_signal for each strategy and return signal results."""
     results = {}
     for strat in self.strategies:
        name = strat.__class__.__name__
        try:
            results[name] = strat.check_signal(df)
        except Exception as e:
            print(f"⚠️ {name} failed: {e}")
            results[name] = None
     return results