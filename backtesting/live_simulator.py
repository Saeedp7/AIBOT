import time
import os
from config.manager import get_config

SYMBOL = get_config("TRADE_SYMBOL", "BTCUSD.")
CHECK_INTERVAL_SECONDS = int(get_config("CHECK_INTERVAL_SECONDS", 60))
from connectors.mt5_connector import initialize_mt5, shutdown_mt5, get_symbol_price
from strategies.strategy_selector import StrategySelector
from execution.order_manager import execute_fake_order
from risk_management.position_sizer import calculate_position_size_and_targets
from utils.trade_logger import log_trade
from ai_engine.strategy_scorer import update_strategy_score
from datetime import datetime
from utils.summary_reporter import generate_daily_summary

def run_simulation():
    if not initialize_mt5():
        print("❌ Failed to initialize MT5")
        return

    balance = 10000
    print(f"🚀 Live Simulation Started. Starting Balance: ${balance}")

    selector = StrategySelector()
    current_position = None
    strategy = None
    last_summary_date = datetime.now().date()

    while True:
        print("\n🔄 Checking market...")

        market_data = selector.fetch_multitimeframe_data(["M15"])
        if not market_data:
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        selected = selector.select_strategy(market_data)
        if not selected:
            print("🔍 Strategy holding, no trade condition met.")
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        strategy = selected
        signal = strategy.signal
        print(f"🔍 Strategy chosen: {strategy.__class__.__name__}")
        print(f"🔍 Buy signal: {signal == 'buy'}")

        if current_position is None and signal in ["buy", "sell"]:
            if getattr(strategy, "last_signal", None) == signal:
                print("⏸️ Signal unchanged, skipping duplicate trade.")
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue
            strategy.last_signal = signal
            entry = get_symbol_price(SYMBOL)
            direction = signal

            volume, stop_loss, tp_levels, regime = calculate_position_size_and_targets(
                entry_price=entry,
                balance=balance,
                strategy_name=strategy.__class__.__name__,
                direction=direction,
                market_data=market_data["M15"],
                symbol=SYMBOL
            )

            current_position = execute_fake_order(
                action=signal,
                symbol=SYMBOL,
                lot_size=volume,
                price=entry,
                sl=stop_loss,
                tp=tp_levels
            )
            if current_position:  # ✅ Only attach metadata if position was created
                 current_position.strategy_name = strategy.__class__.__name__    

        elif current_position is not None:
            price_now = get_symbol_price(SYMBOL)
            current_position.price = price_now
            entry = current_position.price
            sl = current_position.sl
            tp = current_position.tp[0]
            direction = current_position.direction
            volume = current_position.lot_size
            strategy_name = current_position.strategy_name

            result = None
            pnl = 0

            if direction == 'buy':
                if price_now <= sl:
                    print(f"🛑 SL HIT on LONG @ {price_now}")
                    pnl = (price_now - entry) * volume
                    result = "loss"
                    current_position = None
                elif price_now >= tp:
                    print(f"✅ TP HIT on LONG @ {price_now}")
                    pnl = (price_now - entry) * volume
                    result = "win"
                    current_position = None

            elif direction == 'sell':
                if price_now >= sl:
                    print(f"🛑 SL HIT on SHORT @ {price_now}")
                    pnl = (entry - price_now) * volume
                    result = "loss"
                    current_position = None
                elif price_now <= tp:
                    print(f"✅ TP HIT on SHORT @ {price_now}")
                    pnl = (entry - price_now) * volume
                    result = "win"
                    current_position = None

            if result:
                balance += pnl
                log_trade(SYMBOL, direction, entry, price_now, volume, strategy_name, result, pnl, regime)
                update_strategy_score(strategy_name, result)
                print(f"📊 {strategy_name} → {result.upper()} | PnL: ${round(pnl, 2)} | New Balance: ${round(balance, 2)}")

        time.sleep(CHECK_INTERVAL_SECONDS)
        now = datetime.now()
        if now.date() != last_summary_date:
            print("📅 Market day ended. Generating summary...")
            generate_daily_summary()
            last_summary_date = now.date()
    shutdown_mt5()

if __name__ == "__main__":
    run_simulation()