import json
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
# Reuse the existing score management utilities
from ai_engine.strategy_score_manager import update_strategy_score


def run_learning_mode_ml(trade_file="logs/trade_history.json"):
    try:
        with open(trade_file, "r") as f:
            trades = json.load(f)
    except Exception as e:
        print(f"\u26A0\ufe0f Failed to load trade history: {e}")
        return

    df = pd.DataFrame(trades)
    if df.empty or "result" not in df.columns:
        print("\u26A0\ufe0f No usable trades for learning.")
        return

    df["result"] = df["result"].map({"win": 1, "loss": 0})
    df["strategy"] = df["strategy"].astype("category")
    df["symbol"] = df["symbol"].astype("category")
    df["regime"] = df["regime"].astype("category")
    df["hour"] = pd.to_datetime(df["entry_time"]).dt.hour
    df["duration_min"] = df.get("duration_min", 30)

    X = df[["strategy", "symbol", "regime", "hour", "duration_min"]].apply(
        lambda x: x.cat.codes if x.name in ["strategy", "symbol", "regime"] else x
    )
    y = df["result"]

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    print("\U0001F9E0 ML model trained. Re-scoring strategies...")

    strategy_map = dict(enumerate(df["strategy"].cat.categories))
    symbol_map = dict(enumerate(df["symbol"].cat.categories))
    regime_map = dict(enumerate(df["regime"].cat.categories))

    for sid, strategy_name in strategy_map.items():
        for symid, symbol in symbol_map.items():
            for rid, regime in regime_map.items():
                sample = pd.DataFrame(
                    [[sid, symid, rid, 12, 30]],
                    columns=["strategy", "symbol", "regime", "hour", "duration_min"],
                )
                prob = model.predict_proba(sample)[0][1]
                update_strategy_score(strategy_name, symbol, regime, score=prob)

    print("\u2705 Strategy scores updated using ML win probabilities.")