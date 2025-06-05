
This project wraps several modules for interacting with MetaTrader 5 and running strategy logic.

Key modules:

| Module | Description |
| ------ | ----------- |
| `connectors.mt5_connector` | Utility functions for initializing and communicating with the MetaTrader 5 terminal. |
| `data.chart_data_handler` | Fetches OHLCV candles and latest tick prices from MT5. |
| `strategies.*` | Collection of trading strategies used for signal generation. |
| `backtesting.backtest_engine` | Simple engine used in `strategy_backtest.py` for historical simulation. |
| `backtesting.live_simulator` | Runs a paper trading loop using the strategy selector. |

See the comments within each file for more details on usage.