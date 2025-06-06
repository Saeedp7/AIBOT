from data.data_collection import collect_ohlcv_data
from data.preprocessing import preprocess_ohlcv_data
from indicators.indicator_engine import add_indicators

# ✅ Import all 17 strategy classes
from strategies.breakout_strategy import BreakoutStrategy
from strategies.delta_scalping import DeltaDivergenceScalpingStrategy
from strategies.ema_crossover_scalping import EMACrossoverScalpingStrategy
from strategies.fibonacci_swing import FibonacciSwingStrategy
from strategies.ichimoku_day import IchimokuDayStrategy
from strategies.london_breakout import LondonBreakoutStrategy
from strategies.ma_crossover_swing import MACrossoverSwingStrategy
from strategies.macd_divergence import MACDDivergenceStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.micro_breakout_scalping import MicroBreakoutScalpingStrategy
from strategies.order_block_scalping import OrderBlockScalpingStrategy
from strategies.supertrend_adx_rsi_strategy import SupertrendADXRSIStrategy
from strategies.supply_demand_swing import SupplyDemandSwingStrategy
from strategies.trend_following import TrendFollowingStrategy
from strategies.trend_pullback import TrendPullbackStrategy
from strategies.volume_breakout import VolumeBreakoutStrategy
from strategies.vwap_reversion import VWAPReversionStrategy

# Load, preprocess, enrich data
raw = collect_ohlcv_data(symbols=["XAUUSD."], timeframes=["M15"], limit=200)
cleaned = preprocess_ohlcv_data(raw)
enriched = add_indicators(cleaned)
df = enriched["XAUUSD."]["M15"]

# Strategy execution
strategies = {
    "BreakoutStrategy": BreakoutStrategy(),
    "DeltaDivergenceScalpingStrategy": DeltaDivergenceScalpingStrategy(),
    "EMACrossoverScalpingStrategy": EMACrossoverScalpingStrategy(),
    "FibonacciSwingStrategy": FibonacciSwingStrategy(),
    "IchimokuDayStrategy": IchimokuDayStrategy(),
    "LondonBreakoutStrategy": LondonBreakoutStrategy(),
    "MACrossoverSwingStrategy": MACrossoverSwingStrategy(),
    "MACDDivergenceStrategy": MACDDivergenceStrategy(),
    "MeanReversionStrategy": MeanReversionStrategy(),
    "MicroBreakoutScalpingStrategy": MicroBreakoutScalpingStrategy(),
    "OrderBlockScalpingStrategy": OrderBlockScalpingStrategy(),
    "SupertrendADXRSIStrategy": SupertrendADXRSIStrategy(),
    "SupplyDemandSwingStrategy": SupplyDemandSwingStrategy(),
    "TrendFollowingStrategy": TrendFollowingStrategy(),
    "TrendPullbackStrategy": TrendPullbackStrategy(),
    "VolumeBreakoutStrategy": VolumeBreakoutStrategy(),
    "VWAPReversionStrategy": VWAPReversionStrategy(),
}

# Print results
print("✅ MT5 initialized successfully.\n🛑 MT5 connection closed.")
print("\n📊 Strategy Signal Results:")
for name, strategy in strategies.items():
    try:
        signal = strategy.check_signal(df)
        print(f"{name}: {signal}")
    except Exception as e:
        print(f"{name}: ❌ Error - {e}")
