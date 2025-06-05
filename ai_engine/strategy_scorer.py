
from collections import defaultdict
import math
import time
import json
from pathlib import Path

# --- Strategy scoring and performance tracking ---

# Stores scores like: strategy_scores[strategy_name] = {"score": x, "last_updated": timestamp}
strategy_scores = defaultdict(lambda: {"score": 0.0, "last_updated": time.time()})

# Stores regime-based performance: score_by_regime[strategy][regime] = {"wins": x, "losses": y, "score": z}
score_by_regime = defaultdict(lambda: defaultdict(lambda: {"wins": 0, "losses": 0, "score": 0.0}))

# --- Settings ---
DECAY_RATE = 0.95               # Exponential decay rate for score
MIN_STRATEGY_SCORE = -10.0      # Below this score, strategy is considered underperforming
MAX_STRATEGY_SCORE = 20.0       # Cap score to avoid extreme influence

SCORES_PATH = Path(__file__).parent / "strategy_scores.json"

def decay_score(strategy_name):
    now = time.time()
    record = strategy_scores[strategy_name]
    last_update = record["last_updated"]
    elapsed_hours = (now - last_update) / 3600.0

    decay_factor = math.pow(DECAY_RATE, elapsed_hours)
    record["score"] *= decay_factor
    record["last_updated"] = now

def update_strategy_score(strategy_name: str, result: str, regime: str = "unknown"):
    decay_score(strategy_name)
    delta = 1.0 if result == "win" else -1.5
    strategy_scores[strategy_name]["score"] += delta
    strategy_scores[strategy_name]["score"] = min(strategy_scores[strategy_name]["score"], MAX_STRATEGY_SCORE)

    regime_data = score_by_regime[strategy_name][regime]
    if result == "win":
        regime_data["wins"] += 1
        regime_data["score"] += 1
    else:
        regime_data["losses"] += 1
        regime_data["score"] -= 1

    save_strategy_scores({s: data for s, data in strategy_scores.items()})

def get_strategy_score(strategy_name: str) -> float:
    decay_score(strategy_name)
    return strategy_scores[strategy_name]["score"]

def is_strategy_enabled(strategy_name: str) -> bool:
    score = get_strategy_score(strategy_name)
    return score >= MIN_STRATEGY_SCORE

def get_top_strategies(threshold: float = 0.0) -> list:
    return [s for s, meta in strategy_scores.items() if get_strategy_score(s) >= threshold]

def reset_scores():
    strategy_scores.clear()
    score_by_regime.clear()
    save_strategy_scores({})

def print_strategy_scores():
    print("\n📊 Strategy Score Summary:")
    for strat, data in strategy_scores.items():
        print(f" - {strat}: Score = {round(data['score'], 2)}")

def print_regime_scores():
    print("\n📊 Regime-Specific Strategy Scores:")
    for strat, regimes in score_by_regime.items():
        print(f"Strategy: {strat}")
        for regime, perf in regimes.items():
            total = perf["wins"] + perf["losses"]
            winrate = (perf["wins"] / total * 100) if total else 0.0
            print(f"  - {regime}: {perf['wins']}W/{perf['losses']}L | WinRate: {round(winrate,1)}% | Score: {round(perf['score'], 2)}")

def get_strategy_regime_score(strategy_name: str, regime: str) -> float:
    return score_by_regime[strategy_name][regime]["score"]

def is_strategy_suitable(strategy_name: str, regime: str) -> bool:
    return get_strategy_regime_score(strategy_name, regime) >= 0

def get_strategy_win_rate(strategy_name: str, regime: str = None) -> float:
    if regime:
        data = score_by_regime[strategy_name][regime]
    else:
        data = {"wins": 0, "losses": 0}
        for reg in score_by_regime[strategy_name].values():
            data["wins"] += reg["wins"]
            data["losses"] += reg["losses"]
    total = data["wins"] + data["losses"]
    return data["wins"] / total if total > 0 else 0.0

def load_strategy_scores():
    if not SCORES_PATH.exists():
        return {}
    try:
        with open(SCORES_PATH, "r") as f:
            raw = json.load(f)
        for s, data in raw.items():
            strategy_scores[s] = data
        return raw
    except json.JSONDecodeError:
        return {}

def save_strategy_scores(scores):
    with open(SCORES_PATH, "w") as f:
        json.dump(scores, f, indent=2)

if __name__ == "__main__":
    print("🧪 Test Scoring...")
    update_strategy_score("VWAPReversionStrategy", "win", regime="ranging")
    update_strategy_score("VWAPReversionStrategy", "loss", regime="ranging")
    update_strategy_score("VWAPReversionStrategy", "win", regime="ranging")
    update_strategy_score("OrderBlockScalpingStrategy", "loss", regime="trending")
    print_strategy_scores()
    print_regime_scores()
