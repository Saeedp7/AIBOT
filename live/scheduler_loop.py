"""Async scheduler loop utilizing modular components."""

from __future__ import annotations

import asyncio
import logging
import pandas as pd

from execution.order_manager import execute_fake_order
from config.manager import get_config
from utils.market_status import is_market_open

logger = logging.getLogger("scheduler")

FOREX_SYMBOLS = [
    s.strip() for s in get_config("FOREX_SYMBOLS", "XAUUSD.,NDXUSD.,DJIUSD.").split(",") if s.strip()
]
CRYPTO_SYMBOLS = [
    s.strip() for s in get_config("CRYPTO_SYMBOLS", "BTCUSD.,ETHUSD.").split(",") if s.strip()
]
SYMBOLS = FOREX_SYMBOLS + CRYPTO_SYMBOLS
TIMEFRAMES = [t.strip() for t in get_config("TIMEFRAMES", "M5").split(",") if t.strip()]
CHECK_INTERVAL_SECONDS = int(get_config("CHECK_INTERVAL_SECONDS", 60))
MAX_RISK_PER_TRADE = float(get_config("MAX_RISK", 0.01))
active_trades: dict[tuple[str, str], bool] = {}
ACTIVE_SYMBOLS_TIMEFRAMES: dict[str, list[str]] = {}
ohlcv_cache: dict[tuple[str, str], pd.DataFrame] = {}


async def refresh_data(symbol: str, timeframe: str, limit: int = 300) -> None:
    """Fetch and cache OHLCV+indicator data for a symbol/timeframe."""
    DataFetcher, _, _, _ = _lazy_imports(True)
    fetcher = DataFetcher(symbol, timeframe, limit)
    df = await fetcher.fetch()
    if df is not None:
        ohlcv_cache[(symbol, timeframe)] = df


def refresh_active_symbols() -> None:
    """Update ``ACTIVE_SYMBOLS_TIMEFRAMES`` depending on market status."""
    global ACTIVE_SYMBOLS_TIMEFRAMES
    forex_active = [s for s in FOREX_SYMBOLS if is_market_open(s)]
    if forex_active:
        active = forex_active
    else:
        active = [s for s in CRYPTO_SYMBOLS if is_market_open(s)]
    ACTIVE_SYMBOLS_TIMEFRAMES = {s: TIMEFRAMES for s in active}


def active_symbols() -> list[str]:
    refresh_active_symbols()
    return list(ACTIVE_SYMBOLS_TIMEFRAMES.keys())


def _lazy_imports(include_data: bool = True):
    """Import heavy modules on demand."""
    global DataFetcher, SignalProcessor, TradeManager, StrategySelector
    if include_data:
        from core.data_fetcher import DataFetcher  # type: ignore
    else:  # pragma: no cover - fallback when pandas not installed
        DataFetcher = None  # type: ignore
    from core.signal_processor import SignalProcessor
    from core.trade_manager import TradeManager
    from strategies.strategy_selector import StrategySelector
    return DataFetcher, SignalProcessor, TradeManager, StrategySelector

trade_manager = None
selector = None

async def process(symbol: str, timeframe: str) -> None:
    DataFetcher, SignalProcessor, TradeManager, StrategySelector = _lazy_imports(True)
    global trade_manager, selector
    if trade_manager is None:
        trade_manager = TradeManager()
    if selector is None:
        selector = StrategySelector()
    if not is_market_open(symbol):
        return
    try:
        await refresh_data(symbol, timeframe)
        data = ohlcv_cache.get((symbol, timeframe))
        if data is None:
            return
        processor = SignalProcessor(selector.strategies)
        evaluations = await processor.evaluate(data)
        for ev in evaluations:
            sig = ev["signal"]
            direction = sig if isinstance(sig, str) else getattr(sig, "signal", None)
            if direction in {"buy", "sell"}:
                if trade_manager.validate_trade(symbol, MAX_RISK_PER_TRADE):
                    entry = data.iloc[-1]["close"]
                    sl = entry - 1 if direction == "buy" else entry + 1
                    tp = [entry + 2] if direction == "buy" else [entry - 2]
                    trade_manager.execute_trade(symbol, entry, sl, tp)
            break
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Process failure for %s %s: %s", symbol, timeframe, exc)

async def scheduler_loop() -> None:
    while True:
        syms = active_symbols()
        tasks = [process(sym, tf) for sym in syms for tf in TIMEFRAMES]
        await asyncio.gather(*tasks)
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


def execute_trade(direction: str, symbol: str, lot: float, sl: float, tp: float) -> int:
    """Execute a trade (used by tests)."""
    _lazy_imports(False)
    if get_config("LIVE_MODE", "false").lower() != "true":
        execute_fake_order(direction, symbol, lot, 0.0, sl=sl, tp=[tp])
        return 123
    global trade_manager
    if trade_manager is None:
        DataFetcher, SignalProcessor, TradeManager, StrategySelector = _lazy_imports(False)
        trade_manager = TradeManager()
    result = trade_manager.execute_trade(symbol, 0.0, sl, [tp], lot=lot)
    return result.ticket


if __name__ == "__main__":
    asyncio.run(scheduler_loop())
