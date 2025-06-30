# 🧠 AutoTrade AI Bot — README

Welcome to the AutoTrade AI Bot — an intelligent, modular, and fully automated trading engine designed to execute forex and crypto trades across multiple strategies, symbols, and timeframes using MT5.

---

## 🚀 Project Features

* ✅ AI-powered strategy selection
* ✅ Symbol-specific scoring via `strategy_scores_by_asset.json`
* ✅ Modular agent-based architecture
* ✅ Multi-symbol, multi-timeframe support
* ✅ Dynamic SL/TP & breakeven logic
* ✅ Partial take profits (TP1, TP2, TP3)
* ✅ Live trading & backtesting modes
* ✅ Secure MT5 integration via API

---

## 📁 Folder Structure

```
trading_bot_ai/
├── agents/                   # Core logic agents (scanner, executor, memory, etc.)
├── strategies/               # Modular trading strategies
├── risk_management/         # Risk logic and money management modules
├── data/                    # Data fetchers and chart utilities
├── backtesting/             # Backtest engine and live simulator
├── logs/                    # Trade logs, errors, and AI memory
├── config/                  # Settings and environment variables
├── dashboard/               # (Optional) UI dashboard files
└── main.py                  # Master loop to run the bot
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/yourrepo/trading_bot_ai.git
cd trading_bot_ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your MT5 credentials

Edit `config/settings.py` or set environment variables:

```bash
export MT5_LOGIN=123456
export MT5_PASSWORD='your_pass'
export MT5_SERVER='YourBroker-Server'
```

### 4. Run in Live or Backtest Mode

```bash
# Live mode
python main.py

# Backtest mode
python -m backtesting.multi_strategy_backtester
```
### 5. Live Simulation
Set the ``LIVE_MODE`` environment variable to ``false`` to test the loop without
placing real orders. Simulated trades are saved to ``logs/trade_simulated.json``.
```json
[
  {"time": "2025-06-15 14:32:01", "symbol": "XAUUSD.", "direction": "buy", "volume": 0.1}
]
```

Trade manager actions go to `logs/trade_actions.log`:

```
[2025-06-15 14:35:00] XAUUSD. TP1 hit, SL moved to breakeven
```

If the daily risk guard blocks trading, an entry appears in `logs/risk_guard.log`:

```
[2025-06-15 18:00:00] Trade count limit hit: 20 >= 20
```

---

## 📊 AI Strategy Engine

The AI module uses:

* Strategy memory with decay
* Win-rate evaluation
* Regime filters (ranging, trending)
* Multi-agent orchestration (see `AGENTS.md`)

---

## 🛡️ Risk Management

Risk logic includes:

* Max trade size limits
* Daily loss protection
* Take-profit / stop-loss enforcement
* Break-even shifts

Detailed breakdown: [See `RISK_MANAGEMENT.md`](./RISK_MANAGEMENT.md)

---

## 🧪 Strategies Included

* EMA Crossover (scalping)
* MACD Divergence
* VWAP Reversion
* Supply & Demand Swing
* Fibonacci Retracement
* Order Block Scalping
* Ichimoku Trend

Strategy details: [See `STRATEGIES.md`](./STRATEGIES.md)

---

## 🔐 Security Tips

* Use trade-only MT5 accounts
* Never hardcode credentials
* Use environment variables or secure vaults
* Enable logging & review daily logs in `/logs/`

---

## ✅ To-Do / Roadmap

* [x] AI strategy selector
* [x] SL/TP + multi-target logic
* [x] Risk management framework
* [ ] Real-time dashboard UI
* [ ] Reinforcement learning module (experimental)

---

## 🤝 Contributing

Feel free to fork, submit PRs, or suggest improvements. This is an evolving project aimed at real-world auto-trading scalability.

---

## 📩 Contact

Maintained by: **Saeed Pishahang**
Telegram/Instagram: `@Saeedp7`
Email: `dev@autotradeai.net`
