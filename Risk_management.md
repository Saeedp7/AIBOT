# 🛡️ RISK\_MANAGEMENT.md — AutoTrade AI Bot Risk Controls

This document outlines the built-in risk management features used by the AutoTrade AI Bot to prevent account overexposure, reduce drawdown, and protect profits.

---

## 📋 Table of Contents

* [Core Risk Principles](#core-risk-principles)
* [Risk Parameters](#risk-parameters)
* [Stop Loss & Take Profit](#stop-loss--take-profit)
* [Multi-Level TP Logic](#multi-level-tp-logic)
* [BreakEven System](#breakeven-system)
* [Daily Loss Protection](#daily-loss-protection)
* [RiskManagerAgent Workflow](#riskmanageragent-workflow)
* [How to Customize](#how-to-customize)

---

## 🧠 Core Risk Principles

* **Capital preservation is priority #1**
* No trade should expose more than a fixed percentage of capital
* Trades are evaluated **before execution** for risk compliance
* Trade volume, SL/TP, breakeven, and stop-out levels are enforced by code

---

## ⚙️ Risk Parameters

Defined in `config/settings.py` or your preferred config module:

```python
MAX_TRADE_SIZE = 100        # Max dollar amount per trade
DAILY_LOSS_LIMIT_PERCENT = 5.0
TAKE_PROFIT_PERCENT = 2.0
STOP_LOSS_PERCENT = 1.5
```

---

## 🛑 Stop Loss & Take Profit

* SL and TP levels are calculated based on entry price and % thresholds
* Example for \$1000 account:

  * Entry @ \$100
  * TP: \$102 (2%)
  * SL: \$98.5 (1.5%)

---

## 🎯 Multi-Level TP Logic

Enabled for strategies that support scaling out profits. The bot now creates **3
to 5** TP levels based on strategy profile and volatility. Levels are spaced from
the entry price using either ATR multiples or fixed percentages:

* **TP1** — around +1% or *1× ATR*
* **TP2** — around +1.5% or *2× ATR*
* **TP3** — around +2% or *3× ATR*
* **TP4** — +2.5% (*optional*)
* **TP5** — +3% (*optional*)


Once TP1 is hit:

* Stop Loss is moved to **entry (breakeven)**

Once TP2 is hit:

* Stop Loss moves to **TP1 level**

---

## ⚖️ BreakEven System

The breakeven feature automatically protects floating profits:

* If price hits TP1, SL = Entry
* If price hits TP2, SL = TP1
* Ensures worst-case outcome is still profit

The `BreakEvenManager` module tracks these levels and updates the stop loss
accordingly during an open trade.
---

## 🔒 Daily Loss Protection

* If daily drawdown exceeds limit (e.g., -5%), trading is halted for the day
* Calculated from closed trade PnL within session window
* Resets on new trading day (UTC)

---

## 📘 RiskManagerAgent Workflow

1. Receives trade plan from `StrategySelectorAgent`
2. Checks volume, SL, TP, and balance
3. Rejects or adjusts trade if any violation
4. Applies breakeven/TP logic post-entry
5. Monitors for emergency stops

---

## 🛠️ How to Customize

You can extend or override:

* `risk_management/position_sizer.py`
* `risk_management/breakeven_manager.py`
* `risk_management/daily_guard.py`

For advanced setups:

* Use ATR-based SL/TP (`USE_ATR_SL`, `ATR_PERIOD`, `ATR_MULTIPLIER` in `config/settings.py`)
* Enforce time-based stopouts
* Add volatility-based filters
