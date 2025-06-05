# 🤖 AGENTS.md — AutoTrade AI Bot Agents Overview

This document describes the **autonomous agents** and their responsibilities within the AutoTrade AI Bot system. Each agent operates as an independent yet collaborative unit responsible for a core part of the trading workflow.

---

## 📋 Table of Contents

* [Overview](#overview)
* [Agent List](#agent-list)

  * [1. MarketScannerAgent](#1-marketscanneragent)
  * [2. SignalAnalyzerAgent](#2-signalanalyzeragent)
  * [3. StrategySelectorAgent](#3-strategyselectoragent)
  * [4. RiskManagerAgent](#4-riskmanageragent)
  * [5. TradeExecutorAgent](#5-tradeexecutoragent)
  * [6. MemoryEvaluatorAgent](#6-memoryevaluatoragent)
  * [7. MultiSymbolCoordinatorAgent](#7-multisymbolcoordinatoragent)
  * [8. DashboardSyncAgent (Optional)](#8-dashboardsyncagent-optional)
* [Communication & Orchestration](#communication--orchestration)
* [Extending Agents](#extending-agents)

---

## 🧠 Overview

AutoTrade AI Bot utilizes modular intelligent agents to emulate human-like decision-making in real-time trading. Each agent is a service or module that performs a **specific task** in the trading pipeline, designed to be testable, replaceable, and upgradable.

---

## 🔧 Agent List

### 1. 🚀 MarketScannerAgent

**Role:** Continuously monitors live OHLCV data for each symbol and timeframe.

* **Inputs:** Market data stream
* **Outputs:** Raw candlestick data snapshots
* **Key Tasks:**

  * Stream data from broker (via MT5 API)
  * Normalize and forward to SignalAnalyzerAgent

---

### 2. 🧪 SignalAnalyzerAgent

**Role:** Detects actionable signals based on configured strategies.

* **Inputs:** OHLCV data from MarketScannerAgent
* **Outputs:** Signal object(s) with metadata (`buy`, `sell`, `none`)
* **Key Tasks:**

  * Run all enabled strategies
  * Generate signal payloads with confidence, strategy, and SL/TP

---

### 3. 🧠 StrategySelectorAgent

**Role:** Selects the optimal strategy to act upon, using AI memory scoring.

* **Inputs:** Multiple strategy signals
* **Outputs:** Final selected strategy and trade direction
* **Key Tasks:**

  * Evaluate strategy scores using:

    * Regime filters
    * Win-rate memory
    * Decay logic
  * Select or abstain

---

### 4. 🛡️ RiskManagerAgent

**Role:** Enforces risk management rules before trade execution.

* **Inputs:** Final trade plan from StrategySelectorAgent
* **Outputs:** Approved or blocked trade
* **Key Tasks:**

  * Position sizing (fixed, dynamic, AI-based)
  * Check:

    * Max trade size
    * Daily loss limit
    * SL/TP thresholds
    * Account balance
  * Adjust SL/TP dynamically (e.g., BreakEven, trailing)

---

### 5. 🎯 TradeExecutorAgent

**Role:** Sends trades to broker (MT5) and monitors them.

* **Inputs:** Approved trade from RiskManagerAgent
* **Outputs:** Trade ticket, execution status
* **Key Tasks:**

  * Open/close trades
  * Update SL/TP
  * Handle partial TPs (TP1, TP2, TP3)
  * Emergency close conditions

---

### 6. 🧬 MemoryEvaluatorAgent

**Role:** Learns from past trades to refine strategy scoring.

* **Inputs:** Trade logs, outcomes
* **Outputs:** Updated scores and confidence levels
* **Key Tasks:**

  * Log each trade result
  * Score strategies by:

    * Win/loss performance
    * Timeframe/symbol context
    * Regime classification
  * Decay old performance

---

### 7. 🌐 MultiSymbolCoordinatorAgent

**Role:** Manages simultaneous multi-symbol and multi-timeframe scanning and arbitration.

* **Inputs:** Symbol pool (`["XAUUSD", "BTCUSD", "NAS100", ...]`)
* **Outputs:** Orchestrated trade signals across all contexts
* **Key Tasks:**

  * Parallelize scanners
  * Prioritize best trade per context
  * Enforce symbol-specific cooldowns

---

### 8. 📊 DashboardSyncAgent *(Optional)*

**Role:** Feeds dashboard with real-time stats for UI or remote monitoring.

* **Inputs:** All active state objects (trades, signals, memory, equity)
* **Outputs:** WebSocket / API payloads for frontend
* **Key Tasks:**

  * Keep dashboard updated
  * Log user actions if needed

---

## 🔄 Communication & Orchestration

Agents communicate via **shared memory modules**, **queues**, or **publish/subscribe buses** (configurable).

* Default transport: In-process memory (for single-threaded bots)
* For distributed setups: Use Redis pub/sub or ZeroMQ

Orchestration happens in the **MainController loop**:

```python
while True:
    MarketScannerAgent.run()
    SignalAnalyzerAgent.run()
    StrategySelectorAgent.run()
    RiskManagerAgent.run()
    TradeExecutorAgent.run()
    MemoryEvaluatorAgent.update()
    sleep(LOOP_INTERVAL)
```

---

## 🧱 Extending Agents

To add a new agent:

1. Create a new class in `agents/`
2. Define `run()` and/or `evaluate()` methods
3. Register it in the main loop (or conditionally)
4. Update `AGENTS.md` with a new entry

> ✅ **Best Practice:** Keep agents atomic. One responsibility per agent for testability and modularity.

---

## ✅ Status Legend

| Agent                       | Status                |
| --------------------------- | --------------------- |
| MarketScannerAgent          | ✅ Completed           |
| SignalAnalyzerAgent         | ✅ Completed           |
| StrategySelectorAgent       | ✅ Completed           |
| RiskManagerAgent            | ✅ Completed           |
| TradeExecutorAgent          | ✅ Completed           |
| MemoryEvaluatorAgent        | ✅ In Progress         |
| MultiSymbolCoordinatorAgent | 🔄 In Progress        |
| DashboardSyncAgent          | 🕒 Optional / Planned |
