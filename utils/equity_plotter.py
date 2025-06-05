import matplotlib.pyplot as plt
import pandas as pd

def plot_equity_curve(equity_log, save_path="backtesting/equity_curve.png"):
    """
    equity_log: list of (timestamp, balance)
    """
    df = pd.DataFrame(equity_log, columns=['timestamp', 'equity'])
    plt.figure(figsize=(10, 6))
    plt.plot(df['timestamp'], df['equity'], marker='o', linestyle='-')
    plt.title("Equity Curve Over Time")
    plt.xlabel("Time")
    plt.ylabel("Account Balance ($)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"📈 Equity curve saved to {save_path}")
