# tests/conftest.py

import sys
import types

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
    sys.modules["MetaTrader5"] = mt5
