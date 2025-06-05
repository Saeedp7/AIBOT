# 📈 STRATEGIES.md — AutoTrade AI Bot Strategy Library

This document outlines all the built-in strategies used by the AutoTrade AI Bot. Each strategy module outputs actionable trade signals (`buy`, `sell`, or `none`) and includes confidence scoring used by the AI selector engine.

---

## ✅ Active Strategies

### 1. `EMACrossoverScalpingStrategy`

* **Type:** Scalping
* **Indicators:** EMA(9), EMA(21)
* **Signal Logic:**

  * Buy: EMA9 crosses above EMA21
  * Sell: EMA9 crosses below EMA21

---

### 2. `MACDDivergenceStrategy`

* **Type:** Day Trading
* **Indicators:** MACD Histogram
* **Signal Logic:**

  * Detects divergence between MACD and price action
  * Confirms with volume or RSI

---

### 3. `VWAPReversionStrategy`

* **Type:** Scalping / Intraday
* **Indicators:** VWAP, Bollinger Bands
* **Signal Logic:**

  * Buy: Price deviates far below VWAP + BB squeeze
  * Sell: Price spikes above VWAP + reversal candle

---

### 4. `SupplyDemandSwingStrategy`

* **Type:** Swing
* **Indicators:** Supply/Demand zones, trendline validation
* **Signal Logic:**

  * Buy: Demand zone bounce w/ bullish engulfing
  * Sell: Supply zone rejection w/ bearish structure

---

### 5. `FibonacciSwingStrategy`

* **Type:** Swing
* **Indicators:** Fibonacci retracement levels
* **Signal Logic:**

  * Buy: 61.8% retracement + RSI divergence
  * Sell: 78.6% retracement + trend break

---

### 6. `IchimokuDayStrategy`

* **Type:** Day Trading / Trend
* **Indicators:** Ichimoku Cloud (Kumo, Tenkan, Kijun, Chikou)
* **Signal Logic:**

  * Buy: Price > Kumo + Tenkan > Kijun + Chikou breakout
  * Sell: Opposite

---

### 7. `OrderBlockScalpingStrategy`

* **Type:** Scalping
* **Indicators:** Price action, Order block levels, volume
* **Signal Logic:**

  * Buy: OB + bullish BOS + volume spike
  * Sell: OB + bearish BOS + volume surge

---

### 8. `MicroBreakoutScalpingStrategy`

* **Type:** Scalping (low TF)
* **Indicators:** Support/resistance, candle clusters
* **Signal Logic:**

  * Buy: Consolidation + breakout w/ volume
  * Sell: Breakdown w/ wick rejections

---

### 9. `TrendPullbackStrategy`

* **Type:** Day Trading / Trend
* **Indicators:** Trend filter (MA), RSI
* **Signal Logic:**

  * Buy: Uptrend + RSI pullback to 40-50
  * Sell: Downtrend + RSI pullback to 55-65

---

### 10. `DeltaDivergenceScalpingStrategy`

* **Type:** High-frequency scalping
* **Indicators:** Delta Volume, OBV
* **Signal Logic:**

  * Divergence between price and delta/OBV
  * Confirmation via cluster candle / range trap

---

### 11. `VolumeBreakoutStrategy`

* **Type:** Momentum / Breakout
* **Indicators:** Volume spike + breakout pattern
* **Signal Logic:**

  * Buy: Volume surge + resistance breakout
  * Sell: Volume drop + support breakdown

---

### 12. `PatternRecognitionStrategy`

* **Type:** Mixed
* **Indicators:** Chart patterns (wedge, H\&S, triangle)
* **Signal Logic:**

  * Buy/Sell based on pattern breakout direction

---

### 13. `SmartRangeReversalStrategy`

* **Type:** Mean Reversion
* **Indicators:** ATR, pivot zones
* **Signal Logic:**

  * Buy: Oversold at pivot low + low ATR
  * Sell: Overbought at pivot high + squeeze

---

## ⚙️ Strategy Config Example

```json
{
  "strategy": "SupplyDemandSwingStrategy",
  "timeframe": "M15",
  "indicators": {
    "zones": true,
    "trendlines": true
  },
  "entry_conditions": "Demand zone + bullish engulfing",
  "exit_conditions": "Resistance break or TP hit"
}
```

---

## 🧠 Strategy Selection Logic

Each strategy reports its signal and confidence score to the AI engine:

* Strategy score is weighted by:

  * Historical win rate
  * Recent performance
  * Market regime compatibility
* Final strategy is selected by `StrategySelectorAgent`

---

## 🔌 Adding New Strategies

1. Add a new file in `/strategies/`
2. Inherit `BaseStrategy`
3. Implement `generate_signal()` and `name()`
4. Register in `StrategyRegistry`
5. Tune AI score handling if needed
