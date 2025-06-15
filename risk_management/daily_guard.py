import json
import os
from datetime import datetime, timezone
from typing import Optional
from utils.logger import log_risk_guard
from monitoring.alert_manager import alert_daily_guard

try:
    from connectors.mt5_connector import get_account_info
except Exception:
    get_account_info = None


class DailyGuard:
    """Track daily PnL and trade count to enforce risk limits."""

    def __init__(
        self,
        loss_limit_percent: float = 5.0,
        max_trades: int = 20,
        data_file: str = "logs/daily_guard.json",
        starting_balance: Optional[float] = None,
    ) -> None:
        self.loss_limit_percent = loss_limit_percent
        self.max_trades = max_trades
        self.data_file = data_file
        self.starting_balance = starting_balance
        self.state: dict[str, float | int | str] = {}
        self._load_state()

    # -----------------------------------------------------
    def _load_state(self) -> None:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    self.state = json.load(f)
            except Exception:
                self.state = {}
        self.reset_if_new_day()

    def _save_state(self) -> None:
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(self.state, f)

    # -----------------------------------------------------
    def reset_if_new_day(self) -> None:
        current_day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.state.get("date") != current_day:
            balance = self.starting_balance
            if balance is None and get_account_info:
                try:
                    balance = get_account_info().balance
                except Exception:
                    balance = 0.0
            self.state = {"date": current_day, "pnl": 0.0, "trades": 0, "start_balance": balance or 0.0}
            self._save_state()

    # -----------------------------------------------------
    def record_trade(self, pnl: float) -> None:
        self.reset_if_new_day()
        self.state["pnl"] = float(self.state.get("pnl", 0.0)) + float(pnl)
        self.state["trades"] = int(self.state.get("trades", 0)) + 1
        self._save_state()

    def hit_limits(self) -> bool:
        self.reset_if_new_day()
        balance = float(self.state.get("start_balance", 0.0))
        pnl = float(self.state.get("pnl", 0.0))
        pnl_percent = (pnl / balance * 100) if balance > 0 else 0.0
        if pnl_percent <= -self.loss_limit_percent:
            log_risk_guard(
                f"Loss limit hit: {pnl_percent:.2f}% <= -{self.loss_limit_percent}%"
            )
            alert_daily_guard("loss_limit")
            return True
        if int(self.state.get("trades", 0)) >= self.max_trades:
            log_risk_guard(
                f"Trade count limit hit: {self.state.get('trades', 0)} >= {self.max_trades}"
            )
            alert_daily_guard("trade_count")            
            return True
        return False

    def can_trade(self) -> bool:
        return not self.hit_limits()

    # Convenience accessors
    @property
    def trades(self) -> int:
        return int(self.state.get("trades", 0))

    @property
    def pnl(self) -> float:
        return float(self.state.get("pnl", 0.0))