from config.manager import get_config


def estimate_commission(symbol: str, lot: float) -> float:
    """Estimate broker commission cost in USD for the given symbol and lot."""
    rules = get_config("commission_rules", {})
    if isinstance(rules, str):
        # JSON string from env
        try:
            import json
            rules = json.loads(rules)
        except Exception:
            rules = {}
    symbol = symbol.upper().rstrip('.')
    if symbol not in rules:
        return 0.0

    rule = rules[symbol]

    if rule.get("type") == "percent":
        return (float(rule.get("value", 0)) / 100.0) * lot * 100000.0

    if rule.get("type") == "tier":
        for lower, upper, cost in rule.get("tiers", []):
            if lower <= lot <= upper:
                return float(cost) * lot
    return 0.0