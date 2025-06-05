# backtesting/backtest_engine.py

import pandas as pd

class BacktestEngine:
    def __init__(self, strategy, initial_balance=10000, lot_size=0.1, fee_per_trade=0):
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.lot_size = lot_size
        self.fee_per_trade = fee_per_trade
        self.position = None  # 'long' or 'short'
        self.entry_price = None
        self.trades = []

    def run(self, data: pd.DataFrame):
        for i in range(len(data)):
            current_data = data.iloc[:i+1]
            self.strategy.analyze(current_data)

            if self.position is None:
                if self.strategy.should_buy():
                    self.position = 'long'
                    self.entry_price = data.iloc[i]['close']
                    self.trades.append(('BUY', self.entry_price))
                elif self.strategy.should_sell():
                    self.position = 'short'
                    self.entry_price = data.iloc[i]['close']
                    self.trades.append(('SELL', self.entry_price))

            elif self.position == 'long':
                if self.strategy.should_sell():
                    exit_price = data.iloc[i]['close']
                    pnl = (exit_price - self.entry_price) * self.lot_size * 100  # 100 = contract multiplier
                    self.balance += pnl - self.fee_per_trade
                    self.trades.append(('CLOSE LONG', exit_price, pnl))
                    self.position = None
                    self.entry_price = None

            elif self.position == 'short':
                if self.strategy.should_buy():
                    exit_price = data.iloc[i]['close']
                    pnl = (self.entry_price - exit_price) * self.lot_size * 100
                    self.balance += pnl - self.fee_per_trade
                    self.trades.append(('CLOSE SHORT', exit_price, pnl))
                    self.position = None
                    self.entry_price = None

        return self.balance, self.trades

    def reset(self):
        self.balance = self.initial_balance
        self.position = None
        self.entry_price = None
        self.trades = []
