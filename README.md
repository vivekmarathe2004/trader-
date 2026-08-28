# ⚡ VALEXIS QUANT — Autonomous Quantitative Trading Matrix

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat-square&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg?style=flat-square&logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-3178C6.svg?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC.svg?style=flat-square&logo=tailwind-css)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

**VALEXIS QUANT** is an institutional-grade, multi-asset algorithmic trading and autonomous scanning platform built for high reliability, deterministic execution, and hardened risk management. It combines a high-throughput **FastAPI** backend event architecture with a sleek **Next.js 14** glassmorphism trading cockpit.

---

## 🌟 Key Capabilities

### 1. 🤖 Autonomous Trading & Signal Matrix
* **Multi-Strategy Confluence Engine**: Aggregates signals across Trend Following, Mean Reversion, Breakout, Dynamic Momentum, and Volatility Arbitrage.
* **Candlestick Pattern Recognition**: Real-time detection of Pinbars, Engulfing patterns, Morning/Evening Stars, Doji clusters, and Order Blocks.
* **Dynamic Market Regime Classification**: Classifies market context into Trending (Bull/Bear), Mean-Reverting, Ranging, or High-Volatility states.
* **No-Trade Guardrails**: Automatically halts trade generation during low liquidity, excessive spreads, abnormal volatility spikes, or market closed hours.
* **Signal Provenance Tracking**: Every trade decision is backed by an immutable provenance record with indicator snapshots, weights, and entry/exit rationale.

### 2. 🛡️ Unbypassable Hardened Risk Engine
* **Dynamic Position Sizing**: Automatic lot/contract sizing powered by ATR volatility, Account Equity %, or Kelly Criterion.
* **Portfolio Exposure Caps**: Strict limits on max open exposure, maximum open positions per asset class, and per-symbol risk allocations.
* **Drawdown Failsafes & Daily Loss Limits**: Hard-stops trading when daily or cumulative drawdown thresholds are breached.
* **Emergency Global Kill Switch**: One-click instant liquidation and order cancellation across all connected brokers with panic recovery.
* **Reconciliation Daemon**: Continuously compares local order state machine records with live broker positions to eliminate ghost orders and slippage anomalies.

### 3. 🔌 Multi-Broker Execution Matrix
Native integration with top-tier brokers and execution venues:
* **Binance**: Spot and USDⓈ-M Futures REST & WebSocket execution.
* **MetaTrader 5 (MT5)**: Direct IPC connector for Forex, Indices, and Commodities.
* **Deriv**: Synthetics, Volatility Indices, and Forex via WebSocket API.
* **OANDA**: Institutional v20 REST API execution for global FX.
* **Custom Webhook Broker**: Connect custom endpoints or private trading desks.
* **Simulated Mock Broker**: Full zero-risk paper trading environment with realistic slippage and latency simulation.

### 4. 📊 Backtesting & Quantitative Research Lab
* **Event-Driven Backtester**: Multi-asset historical simulation with transaction cost and spread modeling.
* **Monte Carlo Analysis**: Bootstrapping and parametric simulations to evaluate ruin probabilities and drawdown confidence intervals.
* **Sensitivity & Parameter Optimization**: Grid search and parameter stress maps.
* **Walk-Forward Analysis**: Out-of-sample forward verification preventing overfitting.
* **Strategy Promotion Lifecycle**: Automated grading system promoting strategies from Research -> Paper -> Live.

### 5. 💻 Next.js 14 Cyber-Glass Trading Terminal
* Real-time WebSocket streaming telemetry with sub-second health heartbeats.
* Interactive Live Signals scanner, Order Flow inspection modals, and Provenance Explorer.
* Full risk telemetry dashboard with real-time PnL, margin utilization, and broker connection status.
* Responsive dark glassmorphism interface optimized for single-monitor command desks.

---

## 🏛️ System Architecture

`mermaid
graph TD
    subgraph Market_Data["Market Feeds & Telemetry"]
        MD1[Alpha Vantage / Finnhub]
        MD2[Binance Live WS]
        MD3[MT5 Market Data]
        MD4[Deriv Tick Stream]
    end

    subgraph Backend_Core["FastAPI Backend (Port 8000)"]
        UProv[Unified Market Provider]
        Regime[Market Regime & Pattern Engine]
        Strat[Multi-Strategy Confluence Lab]
        NoTrade[No-Trade & Spread Guard]
        AutoTrader[Autonomous Trader Daemon]
        Risk[Hardened Risk Engine & Sizer]
        Failsafe[Failsafe & Kill Switch Monitor]
        Recon[Order Reconciliation Daemon]
        DB[(SQLite / SQLAlchemy Core)]
        Bus[Event Bus & WS Streamer]
    end

    subgraph Execution_Layer["Execution Matrix"]
        B_BIN[Binance Broker]
        B_MT5[MT5 Broker]
        B_DER[Deriv Broker]
        B_OAN[Oanda Broker]
        B_MOCK[Paper / Mock Broker]
    end

    subgraph Frontend_Cockpit["Trading Cockpit (Next.js 14 - Port 3000)"]
        UI_Dash[Overview & PnL Matrix]
        UI_Sig[Live Signals & Scanner]
        UI_Auto[Autonomous Bot Controller]
        UI_Risk[Risk & Health Telemetry]
        UI_Logs[Audit & Provenance Modal]
    end

    Market_Data --> UProv
    UProv --> Regime --> Strat
    Strat --> NoTrade --> AutoTrader
    AutoTrader --> Risk
    Risk --> B_BIN & B_MT5 & B_DER & B_OAN & B_MOCK
    Failsafe -.-> Risk
    Recon -.-> Execution_Layer
    AutoTrader --> DB
    Bus --> Frontend_Cockpit
    Frontend_Cockpit -.->|REST / WebSocket| Backend_Core
`

---

## 📁 Repository Structure

`
Auto-Trader/
├── backend/                        # FastAPI Core Backend
│   ├── app/
│   │   ├── api/v1/                 # REST API endpoints & WebSocket streamer
│   │   ├── backtesting/            # Monte Carlo, Walk-Forward & Optimization
│   │   ├── core/                   # Security, Config & Logging
│   │   ├── database/               # SQLAlchemy Models & Repositories
│   │   ├── events/                 # Pub/Sub Event Bus
│   │   ├── execution/              # Broker Adapters (Binance, MT5, Deriv, Oanda, Mock)
│   │   ├── features/               # Indicators & Price Action Pipelines
│   │   ├── monitoring/             # Health, Failsafe & Attribution
│   │   ├── risk/                   # Hardened Risk Engine & Sizing
│   │   ├── services/               # Market Data Providers & Quality Guards
│   │   └── trading/                # Confluence, AutoTrader, Patterns & Regimes
│   ├── migrations/                 # Alembic Database Migrations
│   ├── tests/                      # Pytest Test Suite
│   └── requirements.txt            # Python Dependencies
│
├── frontend/                       # Next.js 14 Trading Cockpit
│   ├── src/app/
│   │   ├── components/             # Cyber-Glass UI & Modal Components
│   │   ├── markets/                # Real-time Asset Watchlists & Quotes
│   │   ├── operations/             # Auto-Trader, Brokers, Risk, Health & Logs
│   │   ├── signals/                # Live Generated Quantitative Signals
│   │   └── page.tsx                # Main Trading Command Center
│   ├── package.json                # Frontend Dependencies
│   └── tailwind.config.js          # Custom Glassmorphism Theme
│
├── .env.example                    # Environment Configuration Template
├── alembic.ini                     # Database Migration Config
├── pytest.ini                      # Pytest Runner Configuration
├── start.ps1                       # Unified Single-Window Launch Controller (PowerShell)
├── start.bat                       # Windows Batch Launcher
└── Start-Platform.cmd              # One-Click Desktop Platform Launcher
`

---

## 🚀 Quick Start Guide

### Prerequisites
* **Python**: 3.10 or higher
* **Node.js**: 18.x or higher & 
pm
* **Git**

---

### Step 1: Clone the Repository
`ash
git clone https://github.com/vivekmarathe2004/trader-.git
cd trader-
`

---

### Step 2: Configure Environment
Copy the example environment file:
`ash
cp .env.example .env
`
Edit .env to supply your broker credentials and provider keys:
`env
APP_ENV=development
SECRET_KEY=your-super-secure-encryption-key-32-chars

# Master Safety Gate
LIVE_TRADING_ENABLED=false
AUTOTRADER_AUTOSTART_ON_BOOT=false

# Broker Keys (Optional for Simulation/Mock Mode)
BINANCE_API_KEY=
BINANCE_API_SECRET=
DERIV_API_TOKEN=
DERIV_APP_ID=1089
OANDA_API_KEY=
OANDA_ACCOUNT_ID=

# Market Data API Keys
ALPHA_VANTAGE_API_KEY=
FINNHUB_API_KEY=
`

---

### Step 3: Run the Unified Launcher

#### On Windows (Single Window Console):
Run the automated PowerShell controller:
`powershell
.\start.ps1
`
*Or double-click Start-Platform.cmd or start.bat.*

The controller will:
1. Verify background ports (8000, 3000).
2. Boot the FastAPI daemon in the background.
3. Verify /api/v1/health reachability.
4. Launch the Next.js Cockpit on http://localhost:3000.

---

### Step 4: Manual Startup (Alternative)

#### Backend:
`ash
cd backend
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
`
API Documentation will be available at: **http://localhost:8000/docs**

#### Frontend:
`ash
cd frontend
npm install
npm run dev
`
Trading Cockpit will be live at: **http://localhost:3000**

---

## 🧪 Testing & Verification

Run the full backend test suite covering trading strategies, brokers, risk engine, and order state machines:
`ash
cd backend
pytest -v
`

---

## 🛡️ Risk & Safety Notice

> **⚠️ DISCLAIMER**
> Quantitative trading involves substantial risk of loss and is not suitable for every investor. The automated algorithms and tools provided in this repository are for educational, research, and algorithmic development purposes. 
> 
> Always test strategies rigorously in **Mock/Paper Trading mode** before connecting real capital or enabling live execution (LIVE_TRADING_ENABLED=true).

---

## 📜 License

This project is open-sourced under the [MIT License](LICENSE).
