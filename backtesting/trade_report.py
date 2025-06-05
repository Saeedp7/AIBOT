# backtesting/trade_report.py

import pandas as pd

def generate_trade_report(trades, starting_balance=10000):
    """Generate a report from trade history."""

    # Convert trade list to DataFrame
    rows = []
    balance = starting_balance
    peak_balance = starting_balance
    max_drawdown = 0

    for trade in trades:
        if trade[0] in ['CLOSE LONG', 'CLOSE SHORT']:
            exit_price = float(trade[1])
            pnl = float(trade[2])
            rows.append({
                'Type': trade[0],
                'Exit Price': exit_price,
                'PnL': pnl
            })
            balance += pnl
            peak_balance = max(peak_balance, balance)
            drawdown = peak_balance - balance
            max_drawdown = max(max_drawdown, drawdown)

    df = pd.DataFrame(rows)

    total_trades = len(df)
    winning_trades = len(df[df['PnL'] > 0])
    losing_trades = len(df[df['PnL'] <= 0])
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    total_profit = df['PnL'].sum()
    average_pnl = df['PnL'].mean() if total_trades > 0 else 0

    # --- Print Report ---
    print("\n📋 Trade Report Summary:")
    print(f"Total Trades: {total_trades}")
    print(f"Winning Trades: {winning_trades}")
    print(f"Losing Trades: {losing_trades}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Total Profit/Loss: ${total_profit:.2f}")
    print(f"Average PnL per Trade: ${average_pnl:.2f}")
    print(f"Max Drawdown: ${max_drawdown:.2f}")
    print(f"Final Balance: ${balance:.2f}")

    return df  # optional: return dataframe if needed

