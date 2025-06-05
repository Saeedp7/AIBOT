# ai_engine/strategy_config.py

# Support/Resistance sensitivity mapping
# high: avoid trading near S/R
# low: cautious, but may allow trades
# none: ignore S/R zones completely

STRATEGY_TIMEFRAMES = {
    "OrderBlockScalpingStrategy": ["M5"],
    "MicroBreakoutScalpingStrategy": ["M5"],
    "EMACrossoverScalpingStrategy": ["M5", "M15"],
    "DeltaDivergenceScalpingStrategy": ["M5", "M15"],
    "VWAPReversionStrategy": ["M15", "H1"],
    "MACDDivergenceStrategy": ["M15", "H1"],
    "TrendPullbackStrategy": ["H1"],
    "SupplyDemandSwingStrategy": ["H1", "H4"],
    "FibonacciSwingStrategy": ["H1", "H4"],
    "IchimokuDayStrategy": ["H1"],
    "LondonBreakoutStrategy": ["M15", "H1"],
    "VolumeBreakoutStrategy": ["M5", "M15"],
    "PriceActionSwingStrategy": ["H4"],
    "SupportResistanceZoneStrategy": ["H1", "H4"],
    "LiquiditySweepScalpingStrategy": ["M5"],
    "SupertrendADXRSIStrategy": ["M15", "H1", "D1"]
}

STRATEGY_SR_SENSITIVITY = {
    "OrderBlockScalpingStrategy": "high",
    "MicroBreakoutScalpingStrategy": "low",
    "EMACrossoverScalpingStrategy": "none",
    "DeltaDivergenceScalpingStrategy": "low",
    "VWAPReversionStrategy": "low",
    "MACDDivergenceStrategy": "none",
    "TrendPullbackStrategy": "none",
    "SupplyDemandSwingStrategy": "high",
    "FibonacciSwingStrategy": "high",
    "IchimokuDayStrategy": "none",
    "LondonBreakoutStrategy": "low",
    "VolumeBreakoutStrategy": "none",
    "PriceActionSwingStrategy": "high",
    "SupportResistanceZoneStrategy": "high",
    "LiquiditySweepScalpingStrategy": "high",
    "SupertrendADXRSIStrategy": "low"
}

STRATEGY_GROUP = {
    "OrderBlockScalpingStrategy": "scalp",
    "MicroBreakoutScalpingStrategy": "scalp",
    "EMACrossoverScalpingStrategy": "scalp",
    "DeltaDivergenceScalpingStrategy": "scalp",
    "VWAPReversionStrategy": "day",
    "MACDDivergenceStrategy": "day",
    "TrendPullbackStrategy": "day",
    "SupplyDemandSwingStrategy": "swing",
    "FibonacciSwingStrategy": "swing",
    "IchimokuDayStrategy": "day",
    "LondonBreakoutStrategy": "day",
    "VolumeBreakoutStrategy": "scalp",
    "PriceActionSwingStrategy": "swing",
    "SupportResistanceZoneStrategy": "swing",
    "LiquiditySweepScalpingStrategy": "scalp",
    "SupertrendADXRSIStrategy": "day"
}

# Per-strategy S/R tolerance (in points)
STRATEGY_SR_TOLERANCE = {
    "OrderBlockScalpingStrategy": 15,
    "SupplyDemandSwingStrategy": 20,
    "FibonacciSwingStrategy": 25,
    "PriceActionSwingStrategy": 20,
    "SupportResistanceZoneStrategy": 20,
    "LiquiditySweepScalpingStrategy": 10,
    "MicroBreakoutScalpingStrategy": 12,
    "LondonBreakoutStrategy": 15,
    "VWAPReversionStrategy": 12,
    "DeltaDivergenceScalpingStrategy": 10,
    "SupertrendADXRSIStrategy": 8,
    "MACDDivergenceStrategy": 5,
    "EMACrossoverScalpingStrategy": 5,
    "TrendPullbackStrategy": 5,
    "VolumeBreakoutStrategy": 6,
    "IchimokuDayStrategy": 6
}

# Distance tolerance from SR levels before skipping trade
SYMBOL_TOLERANCE_PIPS = {
    "XAUUSD": 10,
    "BTCUSD": 50,
    "ETHUSD": 30,
    "NAS100": 20,
    # Add more as needed
}


