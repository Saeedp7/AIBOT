# force_trade_test.py

from datetime import datetime, timezone
from config.manager import get_config
from risk_management.daily_guard import DailyGuard
from connectors.mt5_connector import get_account_info
from risk_management.lot_sizing_module import calculate_lot_size
from risk_management.stop_loss_manager import determine_sl_tp
from utils.trade_journal import record_trade, update_trade
from utils.logger import log_trade_action
from monitoring.alert_manager import alert_trade_opened
import time

SYMBOL = get_config("FORCE_TRADE_SYMBOL", "BTCUSD.")
TIMEFRAME = get_config("FORCE_TRADE_TIMEFRAME", "M5")
STRATEGY = "ManualTriggerTestStrategy"
DIRECTION = "buy"
ENTRY = 68500.0  # simulated entry price
REGIME = "bullish"

daily_guard = DailyGuard(
    loss_limit_percent=float(get_config("DAILY_LOSS_LIMIT_PERCENT", 5.0)),
    max_trades=int(get_config("MAX_TRADES_PER_DAY", 20))
)

# Check if trade is allowed
print(f"📊 DailyGuard before trade: Trades={daily_guard.state['trades']}," 
      f" PnL={daily_guard.state['pnl']}, CanTrade={daily_guard.can_trade()}")

if not daily_guard.can_trade():
    print("⛔ DailyGuard blocked the trade due to limits.")
else:
    # Simulate SL/TP levels since df is None
    sl = ENTRY - 150 if DIRECTION == "buy" else ENTRY + 150
    tp_levels = [ENTRY + 200, ENTRY + 400, ENTRY + 600] if DIRECTION == "buy" else [ENTRY - 200, ENTRY - 400, ENTRY - 600]

    acct = get_account_info()
    lot = calculate_lot_size(acct.balance, abs(ENTRY - sl), 1.0, SYMBOL)

    # Record trade
    trade_id = int(datetime.now(timezone.utc).timestamp())
    timestamp = datetime.now(timezone.utc).isoformat() + "Z"

    record_trade(
        symbol=SYMBOL,
        timeframe=TIMEFRAME,
        entry=ENTRY,
        sl=sl,
        tps=tp_levels,
        strategy=STRATEGY,
        result="open",
        ticket=trade_id,
        timestamp=timestamp,
        regime=REGIME,
    )

    # Also simulate a skipped trade for confidence test
    low_confidence = 0.12
    log_trade_action(
        f"Confidence {low_confidence:.4f} for {SYMBOL} {TIMEFRAME} using DummyLowConfidenceStrategy"
    )
    log_trade_action(
        f"Skipping trade for {SYMBOL} {TIMEFRAME}: confidence {low_confidence:.4f} < 0.5"
    )


    alert_trade_opened(SYMBOL, TIMEFRAME, DIRECTION, ENTRY, sl, tp_levels[0])
    daily_guard.record_trade(-100)  # Simulate forced PnL impact

    print(f"✅ Forced trade simulated and logged.")

    # Simulate closing the trade after a delay
    time.sleep(0.5)
    update_trade(
        ticket=trade_id,
        result="TP3 hit",
        exit=tp_levels[2],
        close_time=datetime.now(timezone.utc).isoformat() + "Z",
        profit_pct=2.7,
        closed_early=False,
    )

# Final state
print(f"📊 DailyGuard after trade: Trades={daily_guard.state['trades']}," 
      f" PnL={daily_guard.state['pnl']}, CanTrade={daily_guard.can_trade()}")
