# 🤖 AI AutoTrade Bot Development Roadmap

This roadmap outlines the complete plan for evolving your trading bot project around `strategy_backtest.py` into a fully automated, AI-driven MT5 trading system with 90%+ win rate targets. The roadmap is structured by the key features and goals provided.

---

## 🔍 1. Review of `strategy_backtest.py` & Strategy Architecture

* **Purpose:** Central testing file for strategy signals and win tracking
* **Actions:**

  * Extracts OHLCV from `get_ohlcv()`
  * Iterates through strategy list to test signals and win logic
  * Logs signals and calculates win/loss manually (binary scoring)
* **Gaps Identified:**

  * Lacks performance metrics: no drawdown, Sharpe, expectancy
  * No normalization across timeframes/pairs
  * No strategy classification tags (e.g., scalping vs swing)

---

## 📊 2. Strategy Analysis (18 Total)

Each strategy will be analyzed based on:

* Signal clarity (buy/sell/none)
* Ideal market condition (range/trend/volatility)
* Trade frequency (scalping/day/swing)
* SL/TP compatibility
* Backtest win rate

**Proposed Outputs:**

* `strategy_registry.json` with metadata
* `strategy_performance.json` (auto-generated)

**Deliverable:** Strategy audit report & metadata baseline

> ⏱ ETA: 2 days (including scripting tools)

---

## 🧠 3. AI Strategy Selector Design

### Architecture:

* `StrategySelectorAgent`
* `MemoryEvaluatorAgent`
* Scoring model per strategy/timeframe/symbol

### Inputs:

* Live market snapshot
* Recent win/loss performance
* Market regime (ranging/trending/volatile)

### Model:

* Weighted rule-based scoring + neural net (LSTM or decision tree)
* Continuous decay on old data (score aging)

### Storage:

* `strategy_score.json`
* `strategy_thresholds.json`

> ⏱ ETA: 3–4 days for rule-based core, +3 days if using ML

---

## ⚡ 4. Scalping Strategy Optimization

### Scalping Tuning:

* Apply to M1, M5 only
* Add filters:

  * Spread checker
  * Execution slippage buffer
  * Session-aware (avoid news hour)

### Strategy Enhancements:

* Shorter lookback windows (5–20 bars)
* Precision SL/TP (tight: 0.5–1.2% range)
* Monitor execution lag

### Priority Strategies:

* `MicroBreakoutScalping`
* `OrderBlockScalping`
* `VWAPReversion`
* `DeltaDivergenceScalping`

> ⏱ ETA: 2–3 days of tuning + validation

---

## 🕰️ 5. Multi-Timeframe & Multi-Pair Capability

### Required Changes:

* `get_ohlcv(symbol, timeframe)` update for universal access
* Cache & normalize data per context
* `multi_strategy_backtester.py` extension to:

  * Loop through symbols (e.g., XAUUSD, BTCUSD, NAS100, etc.)
  * Loop through TFs (M1, M5, H1, H4)

### Coordination Layer:

* `MultiSymbolCoordinatorAgent`

  * Controls frequency, cooldown, and isolation of each symbol-TF combo

> ⏱ ETA: 3–5 days (data + coordination layer)

---

## 🏆 6. Reaching 90%+ Win Rate

### Key Levers:

* Memory-based strategy switching (avoid low performers)
* Per-market regime fit (trend strategy only in trends)
* Dynamic SL/TP sizing
* Multi-TP exits (TP1, TP2, TP3)
* Filter noise: minimum volume, max spread, max slippage

### Monitoring:

* Daily win rate calculation
* Blacklist strategies with loss streaks > 3

### Optional:

* Reinforcement learning model based on trade logs

> ⏱ ETA: Progressive improvement across all phases

---

## 🤖 7. MT5 Trade Automation

### Action Plan:

* `execute_trade(order_type, symbol, lot, price, sl, tp)`
* Monitor trade lifecycle
* Trigger trade from `TradeExecutorAgent`
* Enable MT5 mock mode for backtesting:

  ```python
  from mock_mt5_interface import *
  ```

### Considerations:

* Real vs demo account safety
* IP whitelisting + no withdrawal key

> ⏱ ETA: 2–3 days full trade pipeline

---

## 🛡️ 8. Advanced Risk Management Module

### Risk Inputs:

* Current balance (from MT5)
* Account equity
* Timeframe sensitivity

### Features:

* Max trade size limit (fixed or % of balance)
* SL/TP ratio enforcement (1:2 min)
* Multi-TP logic:

  * TP1 = 33% closed @ +1%
  * TP2 = 33% closed @ +1.5%
  * TP3 = 34% closed @ +2%
* Breakeven activation (after TP1)
* Daily loss shutdown (e.g., -5%)

### Config Location:

* `config/risk_settings.json`

> ⏱ ETA: 3 days + 1 day testing

---

## 🗂️ Milestones & Deliverables

| Phase | Description                            | Timeline |
| ----- | -------------------------------------- | -------- |
| M1    | Strategy audit & BaseStrategy refactor | 2 days   |
| M2    | AI decision system + memory            | 4–6 days |
| M3    | Scalping enhancements                  | 2–3 days |
| M4    | Multi-TF/symbol rollout                | 3–5 days |
| M5    | Risk & SL/TP optimization              | 3 days   |
| M6    | Full MT5 automation                    | 2–3 days |
| M7    | Final testing & backtest run           | 2 days   |

---

## 🧠 Notes & Assumptions

* Strategies are prebuilt but inconsistent → refactor needed
* MT5 connection layer assumed stable
* Targeting a modular AI + rule hybrid logic for best outcome
* User must actively review trade logs to verify performance improvement

---

## ✅ Final Goal

A robust, multi-strategy, AI-driven MT5 bot with real-time adaptive strategy selection, highly tuned scalping support, cross-timeframe intelligence, dynamic risk control, and a sustainable >90% win rate.

Let me know if you want the next step implemented or scripted (e.g., strategy audit script or AI selector core).
