import os

indicator_keywords = [
    'calculate_ema', 'calculate_sma', 'calculate_rsi', 'calculate_macd',
    'calculate_vwap', 'calculate_supertrend', 'calculate_adx',
    'calculate_bollinger_bands'
]

for file in os.listdir("strategies"):
    if not file.endswith(".py"):
        continue
    with open(f"strategies/{file}", "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        found = any(kw in content for kw in indicator_keywords)
        print(f"{file:<35} → {'✅' if found else '❌ NO INDICATORS'}")

