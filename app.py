"""
Black-Scholes Option Pricing & Analytics Platform
Built with Streamlit & Plotly, powered by unmodified code.py
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import math
import sys
import os

# Import unmodified Black-Scholes engine through loader
import bs_engine_loader as bs

# -------------------------------------------------------------
# Page Configuration & Styling
# -------------------------------------------------------------
st.set_page_config(
    page_title="Black-Scholes Analytics & Option Pricing UI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark fintech theme
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #111827;
        border: 1px solid #1f2937;
        padding: 14px 18px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stMetric"]:hover {
        border-color: #06b6d4;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Courier New', Courier, monospace;
        font-weight: 700;
    }
    /* Tabs */
    button[data-baseweb="tab"] {
        font-weight: 600;
        font-size: 14px;
    }
    /* Highlight badge */
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
    }
    .badge-call {
        background-color: rgba(16, 185, 129, 0.2);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .badge-put {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# Sidebar: Parameter Controls & Presets
# -------------------------------------------------------------
st.sidebar.title("⚙️ Model Parameters")
st.sidebar.caption("All calculations computed via unmodified `code.py`")

# Presets selector
preset = st.sidebar.selectbox(
    "Load Preset Configuration",
    ["Custom", "Standard ATM (1Y, 20% Vol)", "High Volatility / Earnings (30D, 45% Vol)", "LEAPS (2Y, 22% Vol)", "0-DTE Short Expiry (1D, 25% Vol)"],
    index=0
)

# Preset defaults
if preset == "Standard ATM (1Y, 20% Vol)":
    default_S, default_K, default_T, default_v, default_r, default_q = 100.0, 100.0, 1.0, 20.0, 5.0, 0.0
elif preset == "High Volatility / Earnings (30D, 45% Vol)":
    default_S, default_K, default_T, default_v, default_r, default_q = 100.0, 100.0, 30/365, 45.0, 5.0, 0.0
elif preset == "LEAPS (2Y, 22% Vol)":
    default_S, default_K, default_T, default_v, default_r, default_q = 100.0, 105.0, 2.0, 22.0, 4.0, 1.5
elif preset == "0-DTE Short Expiry (1D, 25% Vol)":
    default_S, default_K, default_T, default_v, default_r, default_q = 100.0, 100.0, 1/365, 25.0, 5.0, 0.0
else:
    default_S, default_K, default_T, default_v, default_r, default_q = 100.0, 100.0, 1.0, 20.0, 5.0, 0.0

col_s1, col_s2 = st.sidebar.columns([3, 2])
S = col_s1.number_input("Spot Price (S)", min_value=0.1, max_value=10000.0, value=default_S, step=1.0)
K = col_s1.number_input("Strike Price (K)", min_value=0.1, max_value=10000.0, value=default_K, step=1.0)

time_unit = st.sidebar.radio("Expiration Unit", ["Years", "Days"], horizontal=True)
if time_unit == "Years":
    T = st.sidebar.slider("Time to Maturity (T in Years)", min_value=0.01, max_value=5.0, value=max(0.01, float(default_T)), step=0.01)
    days_val = int(round(T * 365))
    st.sidebar.caption(f"Equivalent: **{days_val} days**")
else:
    days_in = st.sidebar.slider("Time to Maturity (Days)", min_value=1, max_value=1825, value=max(1, int(round(default_T * 365))), step=1)
    T = max(0.001, days_in / 365.0)
    st.sidebar.caption(f"Equivalent: **{T:.3f} years**")

sigma_pct = st.sidebar.slider("Volatility (σ in %)", min_value=1.0, max_value=200.0, value=default_v, step=0.5)
sigma = sigma_pct / 100.0

r_pct = st.sidebar.slider("Risk-Free Rate (r in %)", min_value=0.0, max_value=30.0, value=default_r, step=0.1)
r = r_pct / 100.0

q_pct = st.sidebar.slider("Dividend Yield (q in %)", min_value=0.0, max_value=20.0, value=default_q, step=0.1)
q = q_pct / 100.0

st.sidebar.markdown("---")
st.sidebar.info("💡 **Tip:** Adjust sliders in real-time to observe immediate repricing and Greeks dynamics.")

# -------------------------------------------------------------
# Main Header & Metric Summary
# -------------------------------------------------------------
st.title("📊 Black-Scholes Analytics & Option Pricing Dashboard")
st.markdown("A quantitative platform for European option pricing, Greeks sensitivity analysis, volatility surfaces, and multi-leg strategies — powered by `code.py`.")

# Run calculation via unmodified engine loader
calc = bs.calculate_all(S, K, r, sigma, T, q)
call_p = calc["call_price"]
put_p = calc["put_price"]
g = calc["greeks"]

# Header Metrics Row
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric(
        label="🟢 European Call Price",
        value=f"${call_p:.3f}",
        delta=f"Intrinsic: ${calc['intrinsic_call']:.2f} | Time: ${calc['time_value_call']:.2f}"
    )
with col_m2:
    st.metric(
        label="🔴 European Put Price",
        value=f"${put_p:.3f}",
        delta=f"Intrinsic: ${calc['intrinsic_put']:.2f} | Time: ${calc['time_value_put']:.2f}"
    )
with col_m3:
    moneyness_label = "ATM (At The Money)" if abs(S - K) / K < 0.015 else ("Call ITM / Put OTM" if S > K else "Call OTM / Put ITM")
    st.metric(
        label="🎯 Moneyness Status",
        value=moneyness_label,
        delta=f"Spot/Strike: {(S/K)*100:.1f}%"
    )
with col_m4:
    # Put-Call Parity: C - P = S*e^(-qT) - K*e^(-rT)
    lhs = call_p - put_p
    rhs = S * math.exp(-q * T) - K * math.exp(-r * T)
    parity_diff = abs(lhs - rhs)
    st.metric(
        label="⚖️ Put-Call Parity",
        value=f"Diff: {parity_diff:.2e}",
        delta="Arbitrage-Free Verified" if parity_diff < 1e-4 else "Discrepancy"
    )

st.markdown("---")

# -------------------------------------------------------------
# Greeks Matrix Summary
# -------------------------------------------------------------
st.subheader("⚡ Option Greeks Matrix")
g_col1, g_col2, g_col3, g_col4, g_col5 = st.columns(5)

with g_col1:
    st.metric("Delta (Call / Put)", f"{float(g['Delta(Call)']):.3f} / {float(g['Delta(Put)']):.3f}")
    st.caption("∂V/∂S (Hedge Ratio)")

with g_col2:
    st.metric("Gamma (Γ)", f"{float(g['Gamma']):.5f}")
    st.caption("∂²V/∂S² (Convexity)")

with g_col3:
    st.metric("Vega (𝒱)", f"{float(g['Vega']):.3f}")
    st.caption(f"per 1% σ: ${float(g['Vega'])*0.01:.3f}")

with g_col4:
    # Theta per day
    th_call_d = float(g['Theta(Call)']) / 365.0
    th_put_d = float(g['Theta(Put)']) / 365.0
    st.metric("Theta (Call / Put /day)", f"${th_call_d:.3f} / ${th_put_d:.3f}")
    st.caption("∂V/∂t (Daily Time Decay)")

with g_col5:
    st.metric("Rho (Call / Put)", f"{float(g['Rho(Call)'])*0.01:.3f} / {float(g['Rho(Put)'])*0.01:.3f}")
    st.caption("per 1% rate Δr")

# Intermediate variables expander
with st.expander("🔍 Intermediate Variables ($d_1$, $d_2$, Cumulative Distributions)"):
    d1_val = calc["d1"]
    d2_val = calc["d2"]
    from scipy.stats import norm
    nd1_val = norm.cdf(d1_val)
    nd2_val = norm.cdf(d2_val)
    
    col_d1, col_d2, col_d3, col_d4 = st.columns(4)
    col_d1.markdown(f"**$d_1$ Parameter:** `{d1_val:.5f}`")
    col_d2.markdown(f"**$d_2$ Parameter:** `{d2_val:.5f}`")
    col_d3.markdown(f"**$N(d_1)$ (Call Delta w/o div):** `{nd1_val:.5f}`")
    col_d4.markdown(f"**$N(d_2)$ (Risk-Neutral Exercise Prob):** `{nd2_val:.5f}`")

# -------------------------------------------------------------
# Main Analytics Tabs
# -------------------------------------------------------------
tab_payoff, tab_greeks, tab_heatmaps, tab_surface, tab_iv, tab_strategy, tab_chain, tab_theory = st.tabs([
    "📈 Payoff & Pricing Curves",
    "⚡ Greeks Sensitivity Curves",
    "🗺️ 2D Heatmaps",
    "🧊 3D Volatility Surface",
    "🎯 Implied Volatility Solver",
    "♟️ Strategy Simulator",
    "📋 Option Chain Matrix",
    "📐 Formulas & Theory"
])

# -------------------------------------------------------------
# TAB 1: Payoff & Pricing Curves
# -------------------------------------------------------------
with tab_payoff:
    st.subheader("Option Pricing Curve & Payoff at Expiration")
    
    # Generate spot price array (+- 50% of strike)
    s_min = max(1.0, K * 0.4)
    s_max = K * 1.6
    spots = np.linspace(s_min, s_max, 150)
    
    c_prices = [bs.bs_call(s, K, r, sigma, T, q) for s in spots]
    p_prices = [bs.bs_put(s, K, r, sigma, T, q) for s in spots]
    c_payoffs = [max(0.0, s - K) for s in spots]
    p_payoffs = [max(0.0, K - s) for s in spots]
    
    fig_payoff = go.Figure()
    
    # Call Traces
    fig_payoff.add_trace(go.Scatter(
        x=spots, y=c_prices, mode='lines', name='Call BS Price (Now)',
        line=dict(color='#10b981', width=3)
    ))
    fig_payoff.add_trace(go.Scatter(
        x=spots, y=c_payoffs, mode='lines', name='Call Payoff at Expiry',
        line=dict(color='#34d399', width=1.5, dash='dash')
    ))
    
    # Put Traces
    fig_payoff.add_trace(go.Scatter(
        x=spots, y=p_prices, mode='lines', name='Put BS Price (Now)',
        line=dict(color='#ef4444', width=3)
    ))
    fig_payoff.add_trace(go.Scatter(
        x=spots, y=p_payoffs, mode='lines', name='Put Payoff at Expiry',
        line=dict(color='#f87171', width=1.5, dash='dash')
    ))
    
    # Strike and Spot Vertical Lines
    fig_payoff.add_vline(x=K, line_width=1.5, line_dash="dot", line_color="#818cf8", annotation_text=f"Strike K={K}")
    fig_payoff.add_vline(x=S, line_width=1.5, line_dash="dash", line_color="#38bdf8", annotation_text=f"Current Spot S={S}")
    
    fig_payoff.update_layout(
        template="plotly_dark",
        title=f"Theoretical Option Price vs Underlying Spot Price (K={K}, σ={sigma_pct}%, T={T:.2f}Y)",
        xaxis_title="Underlying Asset Spot Price ($)",
        yaxis_title="Option Value ($)",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_payoff, use_container_width=True)

# -------------------------------------------------------------
# TAB 2: Greeks Sensitivity Curves
# -------------------------------------------------------------
with tab_greeks:
    st.subheader("Greeks Sensitivity Across Spot Price & Time Decay")
    
    greek_choice = st.radio("Select Greek to Visualize", ["Delta (Δ)", "Gamma (Γ)", "Vega (𝒱)", "Theta (Θ)", "Rho (ρ)"], horizontal=True)
    
    # Calculate Greeks across Spot Price
    g_delta_call = []
    g_delta_put = []
    g_gamma = []
    g_vega = []
    g_theta_call = []
    g_theta_put = []
    g_rho_call = []
    g_rho_put = []
    
    for s in spots:
        grk = bs.greeks(s, K, r, sigma, T, q)
        g_delta_call.append(float(grk["Delta(Call)"]))
        g_delta_put.append(float(grk["Delta(Put)"]))
        g_gamma.append(float(grk["Gamma"]))
        g_vega.append(float(grk["Vega"]))
        g_theta_call.append(float(grk["Theta(Call)"]))
        g_theta_put.append(float(grk["Theta(Put)"]))
        g_rho_call.append(float(grk["Rho(Call)"]))
        g_rho_put.append(float(grk["Rho(Put)"]))
        
    fig_greeks = go.Figure()
    
    if greek_choice.startswith("Delta"):
        fig_greeks.add_trace(go.Scatter(x=spots, y=g_delta_call, mode='lines', name='Call Delta', line=dict(color='#10b981', width=3)))
        fig_greeks.add_trace(go.Scatter(x=spots, y=g_delta_put, mode='lines', name='Put Delta', line=dict(color='#ef4444', width=3)))
        fig_greeks.update_layout(yaxis_title="Delta (Hedge Ratio)", yaxis_range=[-1.05, 1.05])
    elif greek_choice.startswith("Gamma"):
        fig_greeks.add_trace(go.Scatter(x=spots, y=g_gamma, mode='lines', name='Gamma (Call & Put)', line=dict(color='#818cf8', width=3)))
        fig_greeks.update_layout(yaxis_title="Gamma (Convexity)")
    elif greek_choice.startswith("Vega"):
        fig_greeks.add_trace(go.Scatter(x=spots, y=g_vega, mode='lines', name='Vega (Sensitivity to Vol)', line=dict(color='#22d3ee', width=3)))
        fig_greeks.update_layout(yaxis_title="Vega ($ per 1.00 σ)")
    elif greek_choice.startswith("Theta"):
        fig_greeks.add_trace(go.Scatter(x=spots, y=g_theta_call, mode='lines', name='Call Theta (Annual)', line=dict(color='#c084fc', width=3)))
        fig_greeks.add_trace(go.Scatter(x=spots, y=g_theta_put, mode='lines', name='Put Theta (Annual)', line=dict(color='#e879f9', width=3)))
        fig_greeks.update_layout(yaxis_title="Theta ($ Decay per Year)")
    elif greek_choice.startswith("Rho"):
        fig_greeks.add_trace(go.Scatter(x=spots, y=g_rho_call, mode='lines', name='Call Rho', line=dict(color='#f472b6', width=3)))
        fig_greeks.add_trace(go.Scatter(x=spots, y=g_rho_put, mode='lines', name='Put Rho', line=dict(color='#fb7185', width=3)))
        fig_greeks.update_layout(yaxis_title="Rho ($ per 100% Rate)")
        
    fig_greeks.add_vline(x=K, line_width=1.5, line_dash="dot", line_color="#94a3b8", annotation_text=f"Strike K={K}")
    fig_greeks.add_vline(x=S, line_width=1.5, line_dash="dash", line_color="#38bdf8", annotation_text=f"Spot S={S}")
    
    fig_greeks.update_layout(
        template="plotly_dark",
        title=f"{greek_choice} vs Spot Price",
        xaxis_title="Underlying Spot Price ($)",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    st.plotly_chart(fig_greeks, use_container_width=True)

# -------------------------------------------------------------
# TAB 3: 2D Heatmaps
# -------------------------------------------------------------
with tab_heatmaps:
    st.subheader("2D Sensitivity Heatmaps (Spot Price vs Volatility)")
    
    target_heatmap = st.selectbox("Select Metric for Heatmap Matrix", ["Call Price ($)", "Put Price ($)", "Call Delta", "Gamma Convexity", "Vega Sensitivity"])
    
    # 2D Grid
    spot_grid = np.linspace(S * 0.7, S * 1.3, 16)
    vol_grid = np.linspace(max(0.05, sigma * 0.4), min(1.2, sigma * 2.2), 14)
    
    matrix = np.zeros((len(vol_grid), len(spot_grid)))
    
    for i, v_val in enumerate(vol_grid):
        for j, s_val in enumerate(spot_grid):
            if target_heatmap == "Call Price ($)":
                matrix[i, j] = bs.bs_call(s_val, K, r, v_val, T, q)
            elif target_heatmap == "Put Price ($)":
                matrix[i, j] = bs.bs_put(s_val, K, r, v_val, T, q)
            elif target_heatmap == "Call Delta":
                matrix[i, j] = float(bs.greeks(s_val, K, r, v_val, T, q)["Delta(Call)"])
            elif target_heatmap == "Gamma Convexity":
                matrix[i, j] = float(bs.greeks(s_val, K, r, v_val, T, q)["Gamma"])
            elif target_heatmap == "Vega Sensitivity":
                matrix[i, j] = float(bs.greeks(s_val, K, r, v_val, T, q)["Vega"])
                
    vol_labels = [f"{v*100:.1f}%" for v in vol_grid]
    spot_labels = [f"${s:.1f}" for s in spot_grid]
    
    fig_heat = px.imshow(
        matrix,
        x=spot_labels,
        y=vol_labels,
        labels=dict(x="Spot Price ($)", y="Volatility (σ)", color=target_heatmap),
        color_continuous_scale="Viridis" if "Call" in target_heatmap else "Magma",
        aspect="auto"
    )
    
    fig_heat.update_layout(
        template="plotly_dark",
        title=f"Sensitivity Matrix: {target_heatmap} (Spot vs Volatility)",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    
    st.plotly_chart(fig_heat, use_container_width=True)

# -------------------------------------------------------------
# TAB 4: 3D Surface
# -------------------------------------------------------------
with tab_surface:
    st.subheader("3D Interactive Volatility & Price Surface (Spot × Time)")
    
    surf_metric = st.selectbox("Select 3D Surface Target", ["Call Option Price", "Put Option Price", "Gamma Surface", "Vega Surface"])
    
    s_mesh = np.linspace(K * 0.6, K * 1.4, 25)
    t_mesh = np.linspace(0.05, max(1.0, T * 1.5), 20)
    S_grid, T_grid = np.meshgrid(s_mesh, t_mesh)
    
    Z = np.zeros_like(S_grid)
    
    for i in range(len(t_mesh)):
        for j in range(len(s_mesh)):
            s_val = S_grid[i, j]
            t_val = T_grid[i, j]
            if surf_metric == "Call Option Price":
                Z[i, j] = bs.bs_call(s_val, K, r, sigma, t_val, q)
            elif surf_metric == "Put Option Price":
                Z[i, j] = bs.bs_put(s_val, K, r, sigma, t_val, q)
            elif surf_metric == "Gamma Surface":
                Z[i, j] = float(bs.greeks(s_val, K, r, sigma, t_val, q)["Gamma"])
            elif surf_metric == "Vega Surface":
                Z[i, j] = float(bs.greeks(s_val, K, r, sigma, t_val, q)["Vega"])
                
    fig_3d = go.Figure(data=[go.Surface(z=Z, x=s_mesh, y=t_mesh, colorscale='Viridis')])
    
    fig_3d.update_layout(
        template="plotly_dark",
        title=f"3D Surface: {surf_metric}",
        scene=dict(
            xaxis_title="Spot Price ($)",
            yaxis_title="Time to Maturity (Yrs)",
            zaxis_title=surf_metric
        ),
        margin=dict(l=20, r=20, t=50, b=20),
        height=650
    )
    
    st.plotly_chart(fig_3d, use_container_width=True)

# -------------------------------------------------------------
# TAB 5: Implied Volatility Solver
# -------------------------------------------------------------
with tab_iv:
    st.subheader("🎯 Implied Volatility Solver (Newton-Raphson)")
    st.markdown("Solve for the market implied volatility using the exact `implied_volatility` routine in `code.py`.")
    
    col_iv1, col_iv2, col_iv3 = st.columns(3)
    with col_iv1:
        iv_type = st.selectbox("Option Type", ["call", "put"])
    with col_iv2:
        market_price = st.number_input("Observed Market Option Price ($)", min_value=0.01, value=10.50, step=0.25)
    with col_iv3:
        iv_strike = st.number_input("Option Strike ($)", min_value=1.0, value=float(K), step=1.0)
        
    if st.button("🚀 Calculate Implied Volatility", type="primary"):
        # Intrinsic check
        intrinsic = max(0.0, S * math.exp(-q*T) - iv_strike * math.exp(-r*T)) if iv_type == "call" else max(0.0, iv_strike * math.exp(-r*T) - S * math.exp(-q*T))
        
        if market_price <= intrinsic:
            st.error(f"Market price (${market_price:.2f}) must be strictly higher than discounted intrinsic value (${intrinsic:.2f}).")
        else:
            try:
                solved_iv = bs.implied_volatility(market_price, S, iv_strike, r, T, type=iv_type, q=q)
                model_check = bs.bs_call(S, iv_strike, r, solved_iv, T, q) if iv_type == "call" else bs.bs_put(S, iv_strike, r, solved_iv, T, q)
                error_margin = abs(market_price - model_check)
                
                st.success(f"**Solved Implied Volatility (IV):** `{solved_iv * 100:.3f}%` (`{solved_iv:.6f}` in decimal)")
                
                col_r1, col_r2, col_r3 = st.columns(3)
                col_r1.metric("Implied Volatility (σ_IV)", f"{solved_iv * 100:.2f}%")
                col_r2.metric("Repriced by BS Model", f"${model_check:.4f}")
                col_r3.metric("Root-Finding Error", f"±{error_margin:.2e}")
                
            except Exception as e:
                st.error(f"Solver failed: {str(e)}")

# -------------------------------------------------------------
# TAB 6: Multi-Leg Strategy Simulator
# -------------------------------------------------------------
with tab_strategy:
    st.subheader("♟️ Options Strategy Payoff & Greeks Simulator")
    
    strat_preset = st.selectbox(
        "Load Strategy Template",
        ["Long Call", "Long Put", "Covered Call", "Protective Put", "Bull Call Spread", "Bear Put Spread", "Long Straddle", "Long Strangle", "Iron Condor"]
    )
    
    # Define Legs based on selection
    if strat_preset == "Long Call":
        legs_def = [{"type": "call", "pos": "buy", "strike": K, "qty": 1}]
    elif strat_preset == "Long Put":
        legs_def = [{"type": "put", "pos": "buy", "strike": K, "qty": 1}]
    elif strat_preset == "Covered Call":
        legs_def = [{"type": "stock", "pos": "buy", "strike": S, "qty": 1}, {"type": "call", "pos": "sell", "strike": round(S*1.05), "qty": 1}]
    elif strat_preset == "Protective Put":
        legs_def = [{"type": "stock", "pos": "buy", "strike": S, "qty": 1}, {"type": "put", "pos": "buy", "strike": round(S*0.95), "qty": 1}]
    elif strat_preset == "Bull Call Spread":
        legs_def = [{"type": "call", "pos": "buy", "strike": round(S*0.95), "qty": 1}, {"type": "call", "pos": "sell", "strike": round(S*1.05), "qty": 1}]
    elif strat_preset == "Bear Put Spread":
        legs_def = [{"type": "put", "pos": "buy", "strike": round(S*1.05), "qty": 1}, {"type": "put", "pos": "sell", "strike": round(S*0.95), "qty": 1}]
    elif strat_preset == "Long Straddle":
        legs_def = [{"type": "call", "pos": "buy", "strike": S, "qty": 1}, {"type": "put", "pos": "buy", "strike": S, "qty": 1}]
    elif strat_preset == "Long Strangle":
        legs_def = [{"type": "put", "pos": "buy", "strike": round(S*0.95), "qty": 1}, {"type": "call", "pos": "buy", "strike": round(S*1.05), "qty": 1}]
    elif strat_preset == "Iron Condor":
        legs_def = [
            {"type": "put", "pos": "buy", "strike": round(S*0.85), "qty": 1},
            {"type": "put", "pos": "sell", "strike": round(S*0.95), "qty": 1},
            {"type": "call", "pos": "sell", "strike": round(S*1.05), "qty": 1},
            {"type": "call", "pos": "buy", "strike": round(S*1.15), "qty": 1}
        ]
        
    # Compute combined PnL
    strat_spots = np.linspace(S * 0.5, S * 1.5, 120)
    total_entry_cost = 0.0
    net_delta = 0.0
    net_gamma = 0.0
    net_vega = 0.0
    net_theta = 0.0
    
    for l in legs_def:
        mult = 1.0 if l["pos"] == "buy" else -1.0
        q_leg = l["qty"]
        stk = l["strike"]
        if l["type"] == "stock":
            total_entry_cost += mult * q_leg * S
            net_delta += mult * q_leg
        elif l["type"] == "call":
            p = bs.bs_call(S, stk, r, sigma, T, q)
            total_entry_cost += mult * q_leg * p
            grk = bs.greeks(S, stk, r, sigma, T, q)
            net_delta += mult * q_leg * float(grk["Delta(Call)"])
            net_gamma += mult * q_leg * float(grk["Gamma"])
            net_vega += mult * q_leg * float(grk["Vega"])
            net_theta += mult * q_leg * float(grk["Theta(Call)"])
        elif l["type"] == "put":
            p = bs.bs_put(S, stk, r, sigma, T, q)
            total_entry_cost += mult * q_leg * p
            grk = bs.greeks(S, stk, r, sigma, T, q)
            net_delta += mult * q_leg * float(grk["Delta(Put)"])
            net_gamma += mult * q_leg * float(grk["Gamma"])
            net_vega += mult * q_leg * float(grk["Vega"])
            net_theta += mult * q_leg * float(grk["Theta(Put)"])
            
    pnl_expiry = []
    pnl_current = []
    
    for s_val in strat_spots:
        exp_v = 0.0
        cur_v = 0.0
        for l in legs_def:
            mult = 1.0 if l["pos"] == "buy" else -1.0
            q_leg = l["qty"]
            stk = l["strike"]
            if l["type"] == "stock":
                exp_v += mult * q_leg * s_val
                cur_v += mult * q_leg * s_val
            elif l["type"] == "call":
                exp_v += mult * q_leg * max(0.0, s_val - stk)
                cur_v += mult * q_leg * bs.bs_call(s_val, stk, r, sigma, T, q)
            elif l["type"] == "put":
                exp_v += mult * q_leg * max(0.0, stk - s_val)
                cur_v += mult * q_leg * bs.bs_put(s_val, stk, r, sigma, T, q)
        pnl_expiry.append(exp_v - total_entry_cost)
        pnl_current.append(cur_v - total_entry_cost)
        
    col_pnl1, col_pnl2, col_pnl3, col_pnl4 = st.columns(4)
    col_pnl1.metric("Net Initial Premium / Cost", f"${total_entry_cost:.2f}")
    col_pnl2.metric("Portfolio Net Delta", f"{net_delta:.3f}")
    col_pnl3.metric("Portfolio Net Gamma", f"{net_gamma:.5f}")
    col_pnl4.metric("Portfolio Net Vega", f"{net_vega:.3f}")
    
    fig_strat = go.Figure()
    fig_strat.add_trace(go.Scatter(x=strat_spots, y=pnl_expiry, mode='lines', name='PnL at Expiry', line=dict(color='#10b981', width=3), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.08)'))
    fig_strat.add_trace(go.Scatter(x=strat_spots, y=pnl_current, mode='lines', name='Current PnL (T > 0)', line=dict(color='#818cf8', width=2, dash='dash')))
    fig_strat.add_hline(y=0, line_width=1, line_color="#94a3b8")
    fig_strat.add_vline(x=S, line_width=1.5, line_dash="dash", line_color="#38bdf8", annotation_text=f"Spot S={S}")
    
    fig_strat.update_layout(
        template="plotly_dark",
        title=f"Strategy Payoff Diagram: {strat_preset}",
        xaxis_title="Underlying Spot Price at Expiry ($)",
        yaxis_title="Net Profit / Loss ($)",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40)
    )
    st.plotly_chart(fig_strat, use_container_width=True)

# -------------------------------------------------------------
# TAB 7: Option Chain Matrix
# -------------------------------------------------------------
with tab_chain:
    st.subheader("📋 Option Chain Matrix")
    
    chain_step = max(1.0, round(S * 0.02, 1))
    center_k = round(S / chain_step) * chain_step
    strikes_list = [round(center_k + (i - 8) * chain_step, 2) for i in range(17)]
    
    chain_rows = []
    for k_val in strikes_list:
        c_p = bs.bs_call(S, k_val, r, sigma, T, q)
        p_p = bs.bs_put(S, k_val, r, sigma, T, q)
        grk = bs.greeks(S, k_val, r, sigma, T, q)
        
        chain_rows.append({
            "Call Price ($)": round(c_p, 3),
            "Call Delta": round(float(grk["Delta(Call)"]), 4),
            "Call Theta/d ($)": round(float(grk["Theta(Call)"]) / 365, 4),
            "Gamma": round(float(grk["Gamma"]), 4),
            "Strike ($)": round(k_val, 2),
            "Vega": round(float(grk["Vega"]) / 100, 4),
            "Put Theta/d ($)": round(float(grk["Theta(Put)"]) / 365, 4),
            "Put Delta": round(float(grk["Delta(Put)"]), 4),
            "Put Price ($)": round(p_p, 3)
        })
        
    df_chain = pd.DataFrame(chain_rows)
    st.dataframe(
        df_chain.style.highlight_max(axis=0, subset=["Gamma", "Vega"], color="#1e3a8a"),
        use_container_width=True,
        hide_index=True
    )
    
    csv_data = df_chain.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Option Chain as CSV",
        data=csv_data,
        file_name=f"black_scholes_chain_S{S}.csv",
        mime="text/csv"
    )

# -------------------------------------------------------------
# TAB 8: Formulas & Theory
# -------------------------------------------------------------
with tab_theory:
    st.subheader("📐 Black-Scholes Analytical Formulas & Derivations")
    
    st.markdown("""
    ### 1. The Black-Scholes-Merton Partial Differential Equation (PDE)
    $$\\frac{\\partial V}{\\partial t} + \\frac{1}{2} \\sigma^2 S^2 \\frac{\\partial^2 V}{\\partial S^2} + (r - q) S \\frac{\\partial V}{\\partial S} - r V = 0$$

    ### 2. European Option Pricing Solutions
    - **European Call Price:**
      $$C(S, K, r, \\sigma, T, q) = S e^{-q T} N(d_1) - K e^{-r T} N(d_2)$$
    - **European Put Price:**
      $$P(S, K, r, \\sigma, T, q) = K e^{-r T} N(-d_2) - S e^{-q T} N(-d_1)$$

    ### 3. Intermediate Standardization Parameters ($d_1$ and $d_2$)
    $$d_1 = \\frac{\\ln(S / K) + \\left(r - q + \\frac{1}{2} \\sigma^2\\right) T}{\\sigma \\sqrt{T}}$$
    $$d_2 = d_1 - \\sigma \\sqrt{T}$$

    ### 4. Option Greeks (Sensitivities)
    | Greek | Mathematical Formula | Economic Interpretation |
    | :--- | :--- | :--- |
    | **Delta (Call)** | $e^{-qT} N(d_1)$ | Rate of change of Call price with respect to underlying asset price |
    | **Delta (Put)** | $e^{-qT} (N(d_1) - 1)$ | Rate of change of Put price with respect to underlying asset price |
    | **Gamma** | $\\frac{e^{-qT} N'(d_1)}{S \\sigma \\sqrt{T}}$ | Rate of change of Delta with respect to asset price (Curvature) |
    | **Vega** | $S e^{-qT} N'(d_1) \\sqrt{T}$ | Sensitivity to volatility $\\sigma$ |
    | **Theta (Call)** | $-\\frac{S N'(d_1) \\sigma e^{-qT}}{2\\sqrt{T}} - r K e^{-rT} N(d_2) + q S e^{-qT} N(d_1)$ | Rate of time decay as expiration approaches |
    | **Theta (Put)** | $-\\frac{S N'(d_1) \\sigma e^{-qT}}{2\\sqrt{T}} + r K e^{-rT} N(-d_2) - q S e^{-qT} N(-d_1)$ | Rate of time decay for Put option |
    | **Rho (Call)** | $K T e^{-rT} N(d_2)$ | Sensitivity to the risk-free interest rate $r$ |
    | **Rho (Put)** | $-K T e^{-rT} N(-d_2)$ | Sensitivity of Put to risk-free rate |
    """)

st.markdown("---")
st.caption("Black-Scholes Dashboard • Pure Execution with unmodified `code.py`")
