
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

The tests under `test_*.py` require the MetaTrader5 module and will fail if it is not available.