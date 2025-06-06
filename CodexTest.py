from ai_engine.score_updater import update_scores, _load_json

# Simulated performance results
new_results = {
    "VWAPReversionStrategy": {"win_rate": 70.0, "recent_score": 1.2, "regime_fit": 1.0},
    "BreakoutStrategy": {"win_rate": 45.0, "recent_score": 0.6}
}

print("🧪 Before update:")
print(_load_json("ai_engine/strategy_scores.json"))

# Run the update
update_scores(new_results)

print("\n✅ After update:")
print(_load_json("ai_engine/strategy_scores.json"))
