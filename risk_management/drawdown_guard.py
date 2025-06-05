# risk_management/drawdown_guard.py

class DrawdownGuard:
    def __init__(self, max_daily_loss_percent=5.0, starting_balance=10000):
        self.max_daily_loss_percent = max_daily_loss_percent
        self.starting_balance = starting_balance
        self.current_balance = starting_balance
        self.trading_halted = False

    def update_balance(self, new_balance):
        """Update balance after each trade and check drawdown."""
        self.current_balance = new_balance
        loss_percent = ((self.starting_balance - self.current_balance) / self.starting_balance) * 100

        if loss_percent >= self.max_daily_loss_percent:
            self.trading_halted = True
            print(f"🛑 Trading Halted! Daily loss limit of {self.max_daily_loss_percent}% reached.")

    def can_trade(self):
        """Check if bot is allowed to trade."""
        return not self.trading_halted
