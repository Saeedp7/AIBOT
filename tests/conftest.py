# tests/conftest.py

import sys
import types
from pathlib import Path

# Mock MetaTrader5 if running on non-Windows
try:
    import MetaTrader5 as mt5
except ImportError:
    print("⚠️ Mocking MetaTrader5 for Codex/Linux testing...")

    mt5 = types.ModuleType("MetaTrader5")
    mt5.initialize = lambda *args, **kwargs: True
    mt5.shutdown = lambda: True
    mt5.order_send = lambda x: {"retcode": 0}
    mt5.last_error = lambda: (0, "Mocked OK")
    mt5.symbol_info = lambda x: {"name": x}
    mt5.symbol_info_tick = lambda x: types.SimpleNamespace(ask=1.0, bid=1.0)
    # basic timeframe constants
    mt5.TIMEFRAME_M1 = 1
    mt5.TIMEFRAME_M5 = 5
    mt5.TIMEFRAME_M15 = 15
    mt5.TIMEFRAME_M30 = 30
    mt5.TIMEFRAME_H1 = 60
    mt5.TIMEFRAME_H4 = 240
    mt5.TIMEFRAME_D1 = 1440
    sys.modules["MetaTrader5"] = mt5


# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Provide lightweight pandas stub if pandas is unavailable
try:
    import pandas  # type: ignore
except Exception:  # pragma: no cover - stub for testing
    pandas = types.ModuleType("pandas")
    class DataFrame:  # minimal placeholder
        pass
    pandas.DataFrame = DataFrame
    class Series:
        pass
    pandas.Series = Series
    sys.modules["pandas"] = pandas

    # stub pandas_ta
    pandas_ta = types.ModuleType("pandas_ta")
    sys.modules["pandas_ta"] = pandas_ta

# Stub requests if missing
try:
    import requests  # type: ignore
except Exception:
    requests = types.ModuleType("requests")
    requests.post = lambda *a, **k: types.SimpleNamespace(status_code=200)
    sys.modules["requests"] = requests
# Stub python-dotenv if missing
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - stub for testing
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *a, **k: None
    sys.modules["dotenv"] = dotenv

# Stub other heavy modules
for name in [
    "data.chart_data_handler",
    "data.preprocessing",
    "indicators.indicator_engine",
    "strategies.strategy_selector",
    "ai_engine.strategy_selector",
]:
    if name not in sys.modules:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
        if name.endswith("chart_data_handler"):
            mod.load_multi_ohlcv = lambda *a, **k: {}
        elif name.endswith("preprocessing"):
            mod.preprocess_ohlcv_data = lambda x: x
        elif name.endswith("indicator_engine"):
            mod.add_indicators = lambda x: x
        elif name.endswith("strategy_selector"):
            mod.StrategySelector = lambda: types.SimpleNamespace(strategies=[])
            mod.load_scores = lambda: {}
            mod.get_best_signal = lambda *a, **k: "buy"

# Stub numpy if missing
try:
    import numpy  # type: ignore
except Exception:
    numpy = types.ModuleType("numpy")
    numpy.std = lambda *a, **k: 0
    sys.modules["numpy"] = numpy