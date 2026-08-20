# 📈 Black-Scholes Option Pricing & Greeks Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Framework](https://img.shields.io/badge/Frontend-TailwindCSS%20%7C%20Chart.js%20%7C%20Plotly-cyan.svg)](https://tailwindcss.com/)
[![Engine](https://img.shields.io/badge/Engine-Unmodified%20code.py-emerald.svg)](#core-engine)

A comprehensive, modern Quantitative Finance analytics dashboard and visualizer built on top of the analytical **Black-Scholes-Merton European Option Pricing Model**.

The platform provides real-time pricing, sensitivity analysis across the **Greeks ($\Delta, \Gamma, \mathcal{V}, \Theta, \rho$)**, 2D sensitivity heatmaps, 3D WebGL volatility surfaces, a Newton-Raphson implied volatility solver, multi-leg options strategy payoff simulation, and option chain matrix generation with CSV export.

---

## 🌟 Key Features

### 1. ⚙️ Interactive Parameter Control & Quick Presets
- Real-time bidirectional sync between sliders and number inputs.
- **Model Parameters:** Spot Price ($S$), Strike Price ($K$), Expiration ($T$ in days/years), Volatility ($\sigma$), Risk-Free Rate ($r$), and Continuous Dividend Yield ($q$).
- **One-Click Presets:** Standard ATM, High Volatility Earnings (30D), LEAPS (2Y), and 0-DTE Short Expiry.

### 2. 📊 Live Pricing & Moneyness Diagnostics
- Real-time theoretical **European Call & Put** prices.
- Dynamic Moneyness status (**ITM**, **ATM**, **OTM**).
- Breakdown into **Intrinsic Value** and **Time Value**.
- Live verification of **Put-Call Parity** ($C - P = S e^{-qT} - K e^{-rT}$).

### 3. ⚡ Complete Greeks Dashboard
- **Delta ($\Delta$):** Hedge ratios for Calls and Puts ($\partial V / \partial S$).
- **Gamma ($\Gamma$):** Curvature and rate of Delta change ($\partial^2 V / \partial S^2$).
- **Vega ($\mathcal{V}$):** Sensitivity per $1\%$ change in volatility ($\partial V / \partial \sigma$).
- **Theta ($\Theta$):** Daily and annual time decay rate ($\partial V / \partial t$).
- **Rho ($\rho$):** Sensitivity to risk-free interest rate fluctuations ($\partial V / \partial r$).
- Intermediate parameters ($d_1, d_2, N(d_1), N(d_2)$).

### 4. 📈 Interactive Visual Analytics Suite
- **Payoff & Theoretical Price Curves:** Black-Scholes current curve vs. expiry payoff with spot and strike price markers.
- **Greeks Sensitivity Curves:** Visualizing Greek changes across spot price ranges and over time decay ($T \to 0$).
- **2D Sensitivity Heatmaps:** Dynamic matrix analyzing option price/Greeks over Spot vs. Volatility grids.
- **3D Interactive Surfaces (WebGL):** 360° rotatable 3D surface plots for option prices and Greeks over Spot $\times$ Expiration.
- **Newton-Raphson Implied Volatility Solver:** Solves for market implied volatility given observed market prices.
- **Multi-Leg Strategy Simulator:** Pre-built and custom strategy modeling (*Bull/Bear Spreads, Covered Call, Protective Put, Straddle, Strangle, Iron Condor*) with net Greeks, breakevens, max profit, and max loss.
- **Option Chain Matrix:** Full chain table across strike prices with ITM/OTM styling and instant **Export to CSV**.
- **Formulas & Mathematical Foundations:** Built-in KaTeX LaTeX reference guide explaining the PDE and analytical solutions.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- `numpy` and `scipy`

```bash
pip install numpy scipy
```

---

### Running the Dashboard

#### Option 1: Standalone Web Dashboard (Instant — Zero Heavy Dependencies)
```bash
python run_ui.py
```
*Or double-click `run_ui.bat` on Windows. This starts the local server and automatically opens **`http://localhost:8000`** in your browser.*

#### Option 2: Streamlit Analytics Platform
```bash
pip install streamlit plotly pandas
streamlit run app.py
```

---

## 📐 Mathematical Formulation

### 1. Black-Scholes-Merton Partial Differential Equation (PDE)
$$\frac{\partial V}{\partial t} + \frac{1}{2} \sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + (r - q) S \frac{\partial V}{\partial S} - r V = 0$$

### 2. European Option Pricing Solutions
$$\begin{aligned}
C(S, K, r, \sigma, T, q) &= S e^{-q T} N(d_1) - K e^{-r T} N(d_2) \\
P(S, K, r, \sigma, T, q) &= K e^{-r T} N(-d_2) - S e^{-q T} N(-d_1)
\end{aligned}$$

where:
$$d_1 = \frac{\ln(S / K) + \left(r - q + \frac{1}{2}\sigma^2\right)T}{\sigma \sqrt{T}}, \quad d_2 = d_1 - \sigma \sqrt{T}$$

### 3. Option Greeks Summary
| Greek | Formula | Financial Interpretation |
| :--- | :--- | :--- |
| **Delta ($\Delta_{Call}$)** | $e^{-qT} N(d_1)$ | Rate of change of Call price w.r.t underlying spot price |
| **Delta ($\Delta_{Put}$)** | $e^{-qT} (N(d_1) - 1)$ | Rate of change of Put price w.r.t underlying spot price |
| **Gamma ($\Gamma$)** | $\frac{e^{-qT} N'(d_1)}{S \sigma \sqrt{T}}$ | Sensitivity of Delta w.r.t spot price (Curvature) |
| **Vega ($\mathcal{V}$)** | $S e^{-qT} N'(d_1) \sqrt{T}$ | Sensitivity of option price w.r.t volatility |
| **Theta ($\Theta_{Call}$)** | $-\frac{S N'(d_1) \sigma e^{-qT}}{2\sqrt{T}} - r K e^{-rT} N(d_2) + q S e^{-qT} N(d_1)$ | Time decay rate as expiry approaches |
| **Theta ($\Theta_{Put}$)** | $-\frac{S N'(d_1) \sigma e^{-qT}}{2\sqrt{T}} + r K e^{-rT} N(-d_2) - q S e^{-qT} N(-d_1)$ | Time decay rate for Put option |
| **Rho ($\rho_{Call}$)** | $K T e^{-rT} N(d_2)$ | Sensitivity w.r.t risk-free interest rate |
| **Rho ($\rho_{Put}$)** | $-K T e^{-rT} N(-d_2)$ | Sensitivity of Put w.r.t risk-free interest rate |

---

## 🏗️ Project Architecture

```
├── Black-Scholes/
│   └── code.py            # Core analytical engine (unmodified, pure math)
├── static/
│   ├── index.html         # Modern web application UI
│   ├── app.js             # Client-side reactivity, Chart.js & Plotly integration
│   └── style.css          # Custom styling, dark mode & glowing accents
├── app.py                 # Streamlit quantitative platform
├── server.py              # Standalone Python HTTP API backend
├── bs_engine_loader.py    # Safe dynamic module loader and wrapper
├── run_ui.py              # Cross-platform 1-click launcher
├── run_ui.bat             # Windows 1-click batch launcher
├── test_ui_api.py         # Automated API & model verification suite
└── README.md              # Project documentation
```

---

## 🔌 API Endpoints Reference

The lightweight backend (`server.py`) exposes REST endpoints:

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/calculate` | `GET` | Computes Call/Put theoretical price, moneyness, intrinsic/time value, and Greeks. |
| `/api/curves` | `GET` | Returns spot range arrays and corresponding prices, payoffs, and Greek curves. |
| `/api/heatmap` | `GET` | Computes a 2D matrix of prices and Greeks over Spot vs. Volatility. |
| `/api/surface` | `GET` | Generates 3D mesh data (Spot $\times$ Time) for WebGL surface rendering. |
| `/api/option_chain` | `GET` | Generates a full strikes chain around current spot with moneyness tags. |
| `/api/implied_vol` | `POST` | Solves for market implied volatility using the Newton-Raphson algorithm. |
| `/api/strategy_payoff`| `POST` | Calculates multi-leg portfolio payoff, net Greeks, and breakeven points. |

---

## 🧪 Testing & Verification

Run the automated test suite to verify calculation accuracy against the analytical engine:
```bash
python test_ui_api.py
```

Expected Output:
```text
Testing GET /api/calculate...
[OK] /api/calculate verified (Call: 10.4506, Put: 5.5735)
Testing GET /api/curves...
[OK] /api/curves verified (80 points generated)
Testing GET /api/heatmap...
[OK] /api/heatmap verified (12x15 matrix)
Testing GET /api/surface...
[OK] /api/surface verified (15x17 mesh)
Testing GET /api/option_chain...
[OK] /api/option_chain verified (15 strikes)
Testing POST /api/implied_vol...
[OK] /api/implied_vol verified (IV: 20.132%)
Testing POST /api/strategy_payoff...
[OK] /api/strategy_payoff verified (Bull Call Spread Cost: $5.33, Max Profit: $4.67)
Testing GET / (Static index.html)...
[OK] Static index.html served successfully

=== ALL TESTS PASSED SUCCESSFULLY! ===
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
