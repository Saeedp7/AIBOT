"""Entry point for AutoTrade AI Bot."""

from __future__ import annotations
import argparse, logging, os
from config.manager import get_config
from connectors.mt5_connector import initialize_mt5, shutdown_mt5
from live.scheduler_loop import scheduler_loop
import asyncio
import MetaTrader5 as mt5
import sys

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AutoTrade AI Bot")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="Run with real order execution")
    mode.add_argument("--test", action="store_true", help="Dry-run without sending orders")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--force-trade",
        action="store_true",
        help="Override guards and force trade execution",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    os.environ["LIVE_MODE"] = "true" if args.live else "false"
    if args.force_trade:
        os.environ["FORCE_TRADE"]  = "true"

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("🟢 Starting AutoTrade AI Bot...")
    if not initialize_mt5():
        print("❌ Unable to connect to MetaTrader5")
        return

    try:
        asyncio.run(scheduler_loop())
    finally:
        shutdown_mt5()
        print("🛑 Bot stopped.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("🛑 Stopping bot...")
        mt5.shutdown()
        sys.exit(0)
