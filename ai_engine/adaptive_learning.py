import json
import os

SCORE_FILE = "ai_memory.json"

def load_scores():
    if not os.path.exists(SCORE_FILE):
        return {}
    with open(SCORE_FILE, "r") as f:
        return json.load(f)

def save_scores(scores):
    with open(SCORE_FILE, "w") as f:
        json.dump(scores, f, indent=4)

def update_strategy_score(strategy_name: str, result: str, learning_rate: float = 0.05, decay: float = 0.005):
    """
    Adjust strategy score based on result (win/loss).
    Increments for wins, decrements for losses.
    Decays all other strategy scores slightly to prioritize recent performers.
    """
    scores = load_scores()

    # Initialize score if not found
    if strategy_name not in scores:
        scores[strategy_name] = 0.5  # neutral starting score

    # Update score based on outcome
    if result == "win":
        scores[strategy_name] += learning_rate
    elif result == "loss":
        scores[strategy_name] -= learning_rate * 1.2  # slightly harsher penalty

    # Clamp between 0 and 1
    scores[strategy_name] = max(0.0, min(1.0, scores[strategy_name]))

    # Apply decay to others
    for strat in scores:
        if strat != strategy_name:
            scores[strat] = max(0.0, scores[strat] - decay)

    save_scores(scores)
