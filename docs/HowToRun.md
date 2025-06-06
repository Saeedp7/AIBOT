## Running the project

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   The project relies on the `MetaTrader5` Python package which requires a local MetaTrader installation.

2. Configure your broker credentials in `config/settings.py` or via environment variables.

3. To run a simple backtest using the trend following strategy:
   ```bash
   python backtesting/strategy_backtest.py
   ```

4. To execute the live simulation (uses a demo account):
   ```bash
   python backtesting/live_simulator.py
   ```

5. To download historical OHLCV data for all configured symbols/timeframes:
   ```bash
   python data/data_collection.py --source MT5 --to-csv
   ```
   Use `--source BINANCE` for Binance data or customize symbols and timeframes
   via additional flags, e.g.:
   Use `--source BINANCE` for Binance data or customize symbols and timeframes via additional flags:
   ```bash
   python data/data_collection.py --source BINANCE --symbols BTCUSDT ETHUSDT \
       --timeframes M5 H1 --to-csv
   ```

The tests under `test_*.py` require the MetaTrader5 module and will fail if it is not available.
6.  The same script can fetch a limited number of bars without saving to CSV:
   ```bash
   python data/data_collection.py --source MT5 --limit 200
   ```

The tests under `test_*.py` require the MetaTrader5 module and will fail if it is not available.