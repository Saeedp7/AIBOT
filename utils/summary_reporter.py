from datetime import datetime
import csv
import json
import os
from collections import defaultdict

def generate_daily_summary():
    log_file = "trade_logs.csv"
    score_file = "strategy_score.json"

    trades = []
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            reader = csv.DictReader(f)
            trades = list(reader)

    summary = {
        "total_trades": 0,
        "win_trades": 0,
        "loss_trades": 0,
        "strategies": defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": 0.0, "regimes": defaultdict(lambda: {"wins": 0, "losses": 0, "pnl": 0.0})}),
        "pnl_total": 0.0
    }

    for trade in trades:
        strategy = trade["Strategy"]
        result = trade["Result"]
        pnl = float(trade["PnL"])
        regime = trade.get("Regime", "unknown")

        summary["total_trades"] += 1
        summary["pnl_total"] += pnl
        if result == "win":
            summary["win_trades"] += 1
            summary["strategies"][strategy]["wins"] += 1
            summary["strategies"][strategy]["regimes"][regime]["wins"] += 1
        elif result == "loss":
            summary["loss_trades"] += 1
            summary["strategies"][strategy]["losses"] += 1
            summary["strategies"][strategy]["regimes"][regime]["losses"] += 1

        summary["strategies"][strategy]["pnl"] += pnl
        summary["strategies"][strategy]["regimes"][regime]["pnl"] += pnl

    print("\n📊 === Daily Summary Report ===")
    print(f"📈 Total Trades: {summary['total_trades']}")
    print(f"✅ Wins: {summary['win_trades']} | ❌ Losses: {summary['loss_trades']}")
    print(f"💰 Net PnL: ${round(summary['pnl_total'], 2)}")

    print("\n🔍 Strategy Breakdown (with Regimes):")
    for strat, data in summary["strategies"].items():
        total = data["wins"] + data["losses"]
        win_rate = (data["wins"] / total) * 100 if total > 0 else 0
        print(f"\n📌 {strat}: {data['wins']}W/{data['losses']}L | Win Rate: {round(win_rate, 1)}% | PnL: ${round(data['pnl'], 2)}")

        for regime, rdata in data["regimes"].items():
            r_total = rdata["wins"] + rdata["losses"]
            r_win_rate = (rdata["wins"] / r_total) * 100 if r_total > 0 else 0
            print(f"   • {regime.capitalize()}: {rdata['wins']}W/{rdata['losses']}L | Win Rate: {round(r_win_rate, 1)}% | PnL: ${round(rdata['pnl'], 2)}")

    print("\n🧠 Strategy memory (from score file):")
    if os.path.exists(score_file):
        with open(score_file, "r") as f:
            scores = json.load(f)
            for strat, s in scores.items():
                wr = (s['wins'] / s['total']) * 100 if s['total'] > 0 else 0
                print(f"    {strat}: {s['wins']}W / {s['losses']}L → {round(wr, 2)}% win rate")

    # Save summary to file
    date_str = datetime.now().strftime("%Y-%m-%d")
    with open(f"daily_summary_{date_str}.txt", "w") as out:
        out.write("=== Daily Summary Report ===\n")
        out.write(f"Total Trades: {summary['total_trades']}\n")
        out.write(f"Wins: {summary['win_trades']} | Losses: {summary['loss_trades']}\n")
        out.write(f"Net PnL: ${round(summary['pnl_total'], 2)}\n\n")
        for strat, data in summary["strategies"].items():
            total = data["wins"] + data["losses"]
            win_rate = (data["wins"] / total) * 100 if total > 0 else 0
            out.write(f"{strat}: {data['wins']}W/{data['losses']}L | Win Rate: {round(win_rate, 1)}% | PnL: ${round(data['pnl'], 2)}\n")
            for regime, rdata in data["regimes"].items():
                r_total = rdata["wins"] + rdata["losses"]
                r_win_rate = (rdata["wins"] / r_total) * 100 if r_total > 0 else 0
                out.write(f"   • {regime.capitalize()}: {rdata['wins']}W/{rdata['losses']}L | Win Rate: {round(r_win_rate, 1)}% | PnL: ${round(rdata['pnl'], 2)}\n")
