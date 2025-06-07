# force_trade_test.py

from datetime import datetime, timezone
from config.manager import get_config
from risk_management.daily_guard import DailyGuard
from connectors.mt5_connector import get_account_info
from risk_management.lot_sizing_module import calculate_lot_size
from risk_management.stop_loss_manager import determine_sl_tp
from utils.trade_journal import record_trade
from utils.logger import log_trade_action
from monitoring.alert_manager import alert_trade_opened

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
    record_trade(
        symbol=SYMBOL,
        timeframe=TIMEFRAME,
        entry=ENTRY,
        sl=sl,
        tps=tp_levels,
        strategy=STRATEGY,
        result="open",
        ticket=trade_id,
        timestamp=datetime.now(timezone.utc).isoformat() + "Z",
    )
    log_trade_action(f"📥 FORCED TRADE {SYMBOL} {TIMEFRAME} @ {ENTRY} | SL: {sl} | TP1: {tp_levels[0]}")
    alert_trade_opened(SYMBOL, TIMEFRAME, DIRECTION, ENTRY, sl, tp_levels[0])
    daily_guard.record_trade(-100)  # Simulate forced PnL impact

    print(f"✅ Forced trade simulated and logged.")

# Final state
print(f"📊 DailyGuard after trade: Trades={daily_guard.state['trades']}," 
      f" PnL={daily_guard.state['pnl']}, CanTrade={daily_guard.can_trade()}")
