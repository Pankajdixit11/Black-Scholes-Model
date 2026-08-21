/**
 * Black-Scholes Dashboard Interactive Logic
 * Seamlessly interfaces with Python backend powered by unmodified code.py
 */

let state = {
    S: 100.0,
    K: 100.0,
    T: 1.0,
    sigma: 0.20,
    r: 0.05,
    q: 0.0,
    activeTab: 'tab-payoff',
    payoffView: 'both',
    greekSelected: 'delta',
    greekAxis: 'spot',
    strategyLegs: [
        { type: 'call', position: 'buy', strike: 100, quantity: 1, premium: 10.45 }
    ]
};

// Global Chart Instances
let chartPayoff = null;
let chartGreeks = null;
let chartStrategy = null;

let debounceTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    setupInputSync();
    initCharts();
    fetchModelData();
    renderMath();
});

function renderMath() {
    if (window.renderMathInElement) {
        renderMathInElement(document.body, {
            delimiters: [
                {left: '$$', right: '$$', display: true},
                {left: '\\[', right: '\\]', display: true},
                {left: '\\(', right: '\\)', display: false},
                {left: '$', right: '$', display: false}
            ],
            throwOnError: false
        });
    }
}

// -------------------------------------------------------------
// Input & Slider Synchronization
// -------------------------------------------------------------
function setupInputSync() {
    const bindings = [
        { num: 'spot-val', slider: 'spot-slider', key: 'S', scale: 1 },
        { num: 'strike-val', slider: 'strike-slider', key: 'K', scale: 1 },
        { num: 'time-val', slider: 'time-slider', key: 'T', scale: 1, onUpdate: updateDaysDisplay },
        { num: 'vol-val', slider: 'vol-slider', key: 'sigma', scale: 0.01 },
        { num: 'rate-val', slider: 'rate-slider', key: 'r', scale: 0.01 },
        { num: 'div-val', slider: 'div-slider', key: 'q', scale: 0.01 },
    ];

    bindings.forEach(b => {
        const numEl = document.getElementById(b.num);
        const sliderEl = document.getElementById(b.slider);

        numEl.addEventListener('input', () => {
            let val = parseFloat(numEl.value);
            if (!isNaN(val)) {
                if (b.scale !== 1) {
                    sliderEl.value = val;
                    state[b.key] = val * b.scale;
                } else {
                    sliderEl.value = val;
                    state[b.key] = val;
                }
                if (b.onUpdate) b.onUpdate(state[b.key]);
                debouncedUpdate();
            }
        });

        sliderEl.addEventListener('input', () => {
            let val = parseFloat(sliderEl.value);
            numEl.value = val;
            state[b.key] = (b.scale !== 1) ? val * b.scale : val;
            if (b.onUpdate) b.onUpdate(state[b.key]);
            debouncedUpdate();
        });
    });
}

function updateDaysDisplay(tVal) {
    const days = Math.round(tVal * 365);
    document.getElementById('days-display').textContent = `${days} days`;
}

function setTimeVal(val) {
    document.getElementById('time-val').value = val.toFixed(3);
    document.getElementById('time-slider').value = val;
    state.T = val;
    updateDaysDisplay(val);
    debouncedUpdate();
}

function debouncedUpdate() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        fetchModelData();
    }, 150);
}

// -------------------------------------------------------------
// Presets
// -------------------------------------------------------------
function applyPreset(preset) {
    if (preset === 'standard') {
        setParams({ S: 100, K: 100, T: 1.0, sigma: 0.20, r: 0.05, q: 0.0 });
    } else if (preset === 'highvol') {
        setParams({ S: 100, K: 100, T: 0.25, sigma: 0.45, r: 0.05, q: 0.0 });
    } else if (preset === 'leaps') {
        setParams({ S: 100, K: 105, T: 2.0, sigma: 0.22, r: 0.04, q: 0.015 });
    } else if (preset === 'zerodte') {
        setParams({ S: 100, K: 100, T: 0.003, sigma: 0.25, r: 0.05, q: 0.0 });
    }
}

function setParams(p) {
    state.S = p.S;
    state.K = p.K;
    state.T = p.T;
    state.sigma = p.sigma;
    state.r = p.r;
    state.q = p.q;

    document.getElementById('spot-val').value = p.S;
    document.getElementById('spot-slider').value = p.S;
    document.getElementById('strike-val').value = p.K;
    document.getElementById('strike-slider').value = p.K;
    document.getElementById('time-val').value = p.T;
    document.getElementById('time-slider').value = p.T;
    updateDaysDisplay(p.T);
    document.getElementById('vol-val').value = (p.sigma * 100).toFixed(1);
    document.getElementById('vol-slider').value = (p.sigma * 100).toFixed(1);
    document.getElementById('rate-val').value = (p.r * 100).toFixed(1);
    document.getElementById('rate-slider').value = (p.r * 100).toFixed(1);
    document.getElementById('div-val').value = (p.q * 100).toFixed(1);
    document.getElementById('div-slider').value = (p.q * 100).toFixed(1);

    debouncedUpdate();
}

function resetDefaults() {
    applyPreset('standard');
}

// -------------------------------------------------------------
// Fetch & Update Model Data
// -------------------------------------------------------------
async function fetchModelData() {
    const url = `/api/calculate?S=${state.S}&K=${state.K}&r=${state.r}&sigma=${state.sigma}&T=${state.T}&q=${state.q}`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        updateSummaryUI(data);

        // Update active tab views
        updateCurves();
        if (state.activeTab === 'tab-heatmap') renderHeatmap();
        if (state.activeTab === 'tab-surface') renderSurface();
        if (state.activeTab === 'tab-chain') updateOptionChain();
        if (state.activeTab === 'tab-strategy') updateStrategyPayoff();
    } catch (err) {
        console.error('Error fetching model data:', err);
    }
}

function updateSummaryUI(data) {
    // Price cards
    document.getElementById('call-price-display').textContent = `$${data.call_price.toFixed(3)}`;
    document.getElementById('put-price-display').textContent = `$${data.put_price.toFixed(3)}`;

    // Moneyness & Intrinsic / Time values
    document.getElementById('call-intrinsic').textContent = `$${data.intrinsic_call.toFixed(2)}`;
    document.getElementById('call-timeval').textContent = `$${data.time_value_call.toFixed(2)}`;
    document.getElementById('put-intrinsic').textContent = `$${data.intrinsic_put.toFixed(2)}`;
    document.getElementById('put-timeval').textContent = `$${data.time_value_put.toFixed(2)}`;

    document.getElementById('call-moneyness-badge').textContent = data.moneyness_call.split(' ')[0];
    document.getElementById('put-moneyness-badge').textContent = data.moneyness_put.split(' ')[0];

    // Greeks
    const g = data.greeks;
    document.getElementById('greek-delta-call').textContent = g['Delta(Call)'].toFixed(4);
    document.getElementById('greek-delta-put').textContent = g['Delta(Put)'].toFixed(4);
    document.getElementById('greek-gamma').textContent = g['Gamma'].toFixed(5);
    document.getElementById('greek-vega').textContent = g['Vega'].toFixed(3);
    document.getElementById('greek-vega-1pct').textContent = `per 1% \u03c3: $${(g['Vega'] * 0.01).toFixed(3)}`;
    
    // Theta (per day = Theta / 365)
    const thetaCallDay = g['Theta(Call)'] / 365;
    const thetaPutDay = g['Theta(Put)'] / 365;
    document.getElementById('greek-theta-call-day').textContent = `$${thetaCallDay.toFixed(4)}`;
    document.getElementById('greek-theta-put-day').textContent = `$${thetaPutDay.toFixed(4)}`;

    document.getElementById('greek-rho-call').textContent = (g['Rho(Call)'] * 0.01).toFixed(4);
    document.getElementById('greek-rho-put').textContent = (g['Rho(Put)'] * 0.01).toFixed(4);

    // Intermediates
    document.getElementById('d1-display').textContent = data.d1.toFixed(4);
    document.getElementById('d2-display').textContent = data.d2.toFixed(4);
    
    // Cumulative normal approximation
    const nd1 = 0.5 * (1 + mathErf(data.d1 / Math.SQRT2));
    const nd2 = 0.5 * (1 + mathErf(data.d2 / Math.SQRT2));
    document.getElementById('nd1-display').textContent = nd1.toFixed(4);
    document.getElementById('nd2-display').textContent = nd2.toFixed(4);

    // Update IV strike default input
    document.getElementById('iv-strike').value = state.K;
}

function mathErf(x) {
    // Approximation of erf
    const a1 =  0.254829592, a2 = -0.284496736, a3 =  1.421413741;
    const a4 = -1.453152027, a5 =  1.061405429, p  =  0.3275911;
    const sign = x < 0 ? -1 : 1;
    x = Math.abs(x);
    const t = 1.0 / (1.0 + p * x);
    const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
    return sign * y;
}

// -------------------------------------------------------------
// Curves & Chart Rendering
// -------------------------------------------------------------
let curvesDataCache = null;

async function updateCurves() {
    const url = `/api/curves?S=${state.S}&K=${state.K}&r=${state.r}&sigma=${state.sigma}&T=${state.T}&q=${state.q}`;
    try {
        const res = await fetch(url);
        curvesDataCache = await res.json();
        renderPayoffChart();
        renderGreeksChart();
    } catch (err) {
        console.error('Error fetching curves:', err);
    }
}

function initCharts() {
    // Common Chart.js Dark Mode Defaults
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = '#1e293b';

    // 1. Payoff Chart
    const ctxPayoff = document.getElementById('chart-payoff').getContext('2d');
    chartPayoff = new Chart(ctxPayoff, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
                tooltip: {
                    backgroundColor: '#0f172a',
                    borderColor: '#334155',
                    borderWidth: 1,
                    padding: 8
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Underlying Asset Price ($)', color: '#64748b' },
                    grid: { color: '#1e293b' }
                },
                y: {
                    title: { display: true, text: 'Option Value / Payoff ($)', color: '#64748b' },
                    grid: { color: '#1e293b' }
                }
            }
        }
    });

    // 2. Greeks Chart
    const ctxGreeks = document.getElementById('chart-greeks').getContext('2d');
    chartGreeks = new Chart(ctxGreeks, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Spot Price ($)', color: '#64748b' },
                    grid: { color: '#1e293b' }
                },
                y: {
                    title: { display: true, text: 'Greek Sensitivity', color: '#64748b' },
                    grid: { color: '#1e293b' }
                }
            }
        }
    });

    // 3. Strategy Chart
    const ctxStrat = document.getElementById('chart-strategy').getContext('2d');
    chartStrategy = new Chart(ctxStrat, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Underlying Spot Price at Expiry ($)', color: '#64748b' },
                    grid: { color: '#1e293b' }
                },
                y: {
                    title: { display: true, text: 'Profit / Loss ($)', color: '#64748b' },
                    grid: { color: '#1e293b' }
                }
            }
        }
    });
}

function renderPayoffChart() {
    if (!curvesDataCache || !chartPayoff) return;
    const d = curvesDataCache;
    const labels = d.spots.map(s => `$${s.toFixed(1)}`);

    const datasets = [];

    if (state.payoffView === 'both' || state.payoffView === 'call') {
        datasets.push({
            label: 'Call BS Value',
            data: d.call_prices,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderWidth: 2.5,
            pointRadius: 0,
            tension: 0.1
        });
        datasets.push({
            label: 'Call Payoff (Expiry)',
            data: d.spots.map(s => Math.max(0, s - state.K)),
            borderColor: '#34d399',
            borderWidth: 1.5,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false
        });
    }

    if (state.payoffView === 'both' || state.payoffView === 'put') {
        datasets.push({
            label: 'Put BS Value',
            data: d.put_prices,
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            borderWidth: 2.5,
            pointRadius: 0,
            tension: 0.1
        });
        datasets.push({
            label: 'Put Payoff (Expiry)',
            data: d.spots.map(s => Math.max(0, state.K - s)),
            borderColor: '#f87171',
            borderWidth: 1.5,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false
        });
    }

    chartPayoff.data.labels = labels;
    chartPayoff.data.datasets = datasets;
    chartPayoff.update();
}

function setPayoffView(view) {
    state.payoffView = view;
    ['both', 'call', 'put'].forEach(v => {
        const btn = document.getElementById(`payoff-view-${v}`);
        if (v === view) {
            btn.className = 'px-2.5 py-1 rounded bg-cyan-600/30 text-cyan-300 border border-cyan-500/40';
        } else {
            btn.className = 'px-2.5 py-1 rounded bg-gray-800 text-gray-400 hover:bg-gray-700';
        }
    });
    renderPayoffChart();
}

function renderGreeksChart() {
    if (!curvesDataCache || !chartGreeks) return;
    const d = curvesDataCache;

    let labels = [];
    const datasets = [];

    if (state.greekAxis === 'spot') {
        labels = d.spots.map(s => `$${s.toFixed(1)}`);
        chartGreeks.options.scales.x.title.text = 'Spot Price ($)';

        if (state.greekSelected === 'delta') {
            datasets.push({
                label: 'Call Delta',
                data: d.delta_calls,
                borderColor: '#10b981',
                borderWidth: 2.5,
                pointRadius: 0
            });
            datasets.push({
                label: 'Put Delta',
                data: d.delta_puts,
                borderColor: '#ef4444',
                borderWidth: 2.5,
                pointRadius: 0
            });
        } else if (state.greekSelected === 'gamma') {
            datasets.push({
                label: 'Gamma (\u0393)',
                data: d.gammas,
                borderColor: '#818cf8',
                borderWidth: 2.5,
                pointRadius: 0
            });
        } else if (state.greekSelected === 'vega') {
            datasets.push({
                label: 'Vega (\u03bd)',
                data: d.vegas,
                borderColor: '#22d3ee',
                borderWidth: 2.5,
                pointRadius: 0
            });
        } else if (state.greekSelected === 'theta') {
            datasets.push({
                label: 'Call Theta (per year)',
                data: d.theta_calls,
                borderColor: '#c084fc',
                borderWidth: 2.5,
                pointRadius: 0
            });
            datasets.push({
                label: 'Put Theta (per year)',
                data: d.theta_puts,
                borderColor: '#e879f9',
                borderWidth: 2.5,
                pointRadius: 0
            });
        } else if (state.greekSelected === 'rho') {
            datasets.push({
                label: 'Call Rho',
                data: d.rho_calls,
                borderColor: '#f472b6',
                borderWidth: 2.5,
                pointRadius: 0
            });
            datasets.push({
                label: 'Put Rho',
                data: d.rho_puts,
                borderColor: '#fb7185',
                borderWidth: 2.5,
                pointRadius: 0
            });
        }
    } else {
        // vs Time to Expiry
        labels = d.times.map(t => `${t.toFixed(2)}Y`);
        chartGreeks.options.scales.x.title.text = 'Time to Expiry (Years)';

        if (state.greekSelected === 'theta') {
            datasets.push({
                label: 'Call Theta decay',
                data: d.time_thetas,
                borderColor: '#c084fc',
                borderWidth: 2.5,
                pointRadius: 0
            });
        } else {
            datasets.push({
                label: 'Call Price Decay',
                data: d.time_call_prices,
                borderColor: '#10b981',
                borderWidth: 2.5,
                pointRadius: 0
            });
            datasets.push({
                label: 'Put Price Decay',
                data: d.time_put_prices,
                borderColor: '#ef4444',
                borderWidth: 2.5,
                pointRadius: 0
            });
        }
    }

    chartGreeks.data.labels = labels;
    chartGreeks.data.datasets = datasets;
    chartGreeks.update();
}

function setGreekCurve(greek) {
    state.greekSelected = greek;
    ['delta', 'gamma', 'vega', 'theta', 'rho'].forEach(g => {
        const btn = document.getElementById(`gc-btn-${g}`);
        if (g === greek) {
            btn.className = 'px-2.5 py-1 rounded bg-cyan-600/30 text-cyan-300 border border-cyan-500/40';
        } else {
            btn.className = 'px-2.5 py-1 rounded bg-gray-800 text-gray-400 hover:bg-gray-700';
        }
    });
    renderGreeksChart();
}

function setGreekAxis(axis) {
    state.greekAxis = axis;
    const spotBtn = document.getElementById('ga-btn-spot');
    const timeBtn = document.getElementById('ga-btn-time');
    if (axis === 'spot') {
        spotBtn.className = 'px-2.5 py-1 rounded bg-indigo-600/30 text-indigo-300 border border-indigo-500/40';
        timeBtn.className = 'px-2.5 py-1 rounded bg-gray-800 text-gray-400 hover:bg-gray-700';
    } else {
        timeBtn.className = 'px-2.5 py-1 rounded bg-indigo-600/30 text-indigo-300 border border-indigo-500/40';
        spotBtn.className = 'px-2.5 py-1 rounded bg-gray-800 text-gray-400 hover:bg-gray-700';
    }
    renderGreeksChart();
}

// -------------------------------------------------------------
// 2D Heatmaps (Plotly)
// -------------------------------------------------------------
async function renderHeatmap() {
    const url = `/api/heatmap?S=${state.S}&K=${state.K}&r=${state.r}&sigma=${state.sigma}&T=${state.T}&q=${state.q}`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        const target = document.getElementById('heatmap-select').value;

        let zData = data.call_matrix;
        let title = 'Call Price ($)';
        let colorscale = 'Viridis';

        if (target === 'put') {
            zData = data.put_matrix;
            title = 'Put Price ($)';
            colorscale = 'Magma';
        } else if (target === 'delta') {
            zData = data.call_delta_matrix;
            title = 'Call Delta';
            colorscale = 'Electric';
        } else if (target === 'gamma') {
            zData = data.gamma_matrix;
            title = 'Gamma Convexity';
            colorscale = 'Plasma';
        } else if (target === 'vega') {
            zData = data.vega_matrix;
            title = 'Vega Sensitivity';
            colorscale = 'Cyan';
        }

        const plotData = [{
            z: zData,
            x: data.spots,
            y: data.vols,
            type: 'heatmap',
            colorscale: colorscale,
            hoverongaps: false
        }];

        const layout = {
            title: { text: `${title} Matrix (Spot vs Volatility)`, font: { color: '#e2e8f0', size: 13 } },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            xaxis: { title: 'Spot Price ($)', color: '#94a3b8', gridcolor: '#1e293b' },
            yaxis: { title: 'Volatility (%)', color: '#94a3b8', gridcolor: '#1e293b' },
            margin: { l: 60, r: 20, t: 40, b: 50 },
            font: { family: 'sans-serif', color: '#94a3b8' }
        };

        Plotly.newPlot('plotly-heatmap', plotData, layout, { responsive: true, displayModeBar: false });
    } catch (err) {
        console.error('Heatmap error:', err);
    }
}

// -------------------------------------------------------------
// 3D Surface (Plotly)
// -------------------------------------------------------------
async function renderSurface() {
    const url = `/api/surface?S=${state.S}&K=${state.K}&r=${state.r}&sigma=${state.sigma}&q=${state.q}`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        const target = document.getElementById('surface-select').value;

        let zData = data.call_z;
        let title = 'Call Price Surface';
        let colorscale = 'Viridis';

        if (target === 'put') {
            zData = data.put_z;
            title = 'Put Price Surface';
            colorscale = 'Hot';
        } else if (target === 'gamma') {
            zData = data.gamma_z;
            title = 'Gamma Convexity Surface';
            colorscale = 'Plasma';
        } else if (target === 'vega') {
            zData = data.vega_z;
            title = 'Vega Surface';
            colorscale = 'Cool';
        }

        const plotData = [{
            z: zData,
            x: data.spots,
            y: data.times,
            type: 'surface',
            colorscale: colorscale,
            contours: {
                z: { show: true, usecolormap: true, highlightcolor: "#42f4eb", project: { z: true } }
            }
        }];

        const layout = {
            title: { text: `${title} (Spot \u00d7 Expiry)`, font: { color: '#e2e8f0', size: 13 } },
            paper_bgcolor: 'transparent',
            margin: { l: 10, r: 10, t: 40, b: 10 },
            scene: {
                xaxis: { title: 'Spot ($)', color: '#94a3b8', backgroundcolor: '#0f172a', gridcolor: '#1e293b' },
                yaxis: { title: 'Time (Yrs)', color: '#94a3b8', backgroundcolor: '#0f172a', gridcolor: '#1e293b' },
                zaxis: { title: 'Value', color: '#94a3b8', backgroundcolor: '#0f172a', gridcolor: '#1e293b' },
                camera: { eye: { x: 1.5, y: -1.5, z: 1.2 } }
            }
        };

        Plotly.newPlot('plotly-surface', plotData, layout, { responsive: true, displayModeBar: true });
    } catch (err) {
        console.error('Surface error:', err);
    }
}

// -------------------------------------------------------------
// Implied Volatility Solver
// -------------------------------------------------------------
async function calculateIV() {
    const marketPrice = parseFloat(document.getElementById('iv-market-price').value);
    const optType = document.getElementById('iv-type').value;
    const strike = parseFloat(document.getElementById('iv-strike').value);

    try {
        const res = await fetch('/api/implied_vol', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                price: marketPrice,
                S: state.S,
                K: strike,
                r: state.r,
                T: state.T,
                type: optType,
                q: state.q
            })
        });

        const data = await res.json();
        const box = document.getElementById('iv-result-box');

        if (res.ok) {
            box.classList.remove('hidden');
            document.getElementById('iv-result-val').textContent = `${data.implied_volatility_pct}%`;
            document.getElementById('iv-decimal').textContent = data.implied_volatility.toFixed(4);
            document.getElementById('iv-recovered').textContent = `$${data.recovered_price.toFixed(3)}`;
            document.getElementById('iv-error').textContent = `\u00b1${data.error_margin.toFixed(6)}`;
        } else {
            alert(`Error: ${data.error || 'Failed to solve IV'}`);
        }
    } catch (err) {
        alert(`Request failed: ${err.message}`);
    }
}

// -------------------------------------------------------------
// Strategy Simulator
// -------------------------------------------------------------
function loadStrategyPreset(preset) {
    const s = state.S;
    if (preset === 'long_call') {
        state.strategyLegs = [{ type: 'call', position: 'buy', strike: s, quantity: 1, premium: 0 }];
    } else if (preset === 'long_put') {
        state.strategyLegs = [{ type: 'put', position: 'buy', strike: s, quantity: 1, premium: 0 }];
    } else if (preset === 'covered_call') {
        state.strategyLegs = [
            { type: 'stock', position: 'buy', strike: s, quantity: 1, premium: s },
            { type: 'call', position: 'sell', strike: Math.round(s * 1.05), quantity: 1, premium: 0 }
        ];
    } else if (preset === 'protective_put') {
        state.strategyLegs = [
            { type: 'stock', position: 'buy', strike: s, quantity: 1, premium: s },
            { type: 'put', position: 'buy', strike: Math.round(s * 0.95), quantity: 1, premium: 0 }
        ];
    } else if (preset === 'bull_call_spread') {
        state.strategyLegs = [
            { type: 'call', position: 'buy', strike: Math.round(s * 0.95), quantity: 1, premium: 0 },
            { type: 'call', position: 'sell', strike: Math.round(s * 1.05), quantity: 1, premium: 0 }
        ];
    } else if (preset === 'bear_put_spread') {
        state.strategyLegs = [
            { type: 'put', position: 'buy', strike: Math.round(s * 1.05), quantity: 1, premium: 0 },
            { type: 'put', position: 'sell', strike: Math.round(s * 0.95), quantity: 1, premium: 0 }
        ];
    } else if (preset === 'long_straddle') {
        state.strategyLegs = [
            { type: 'call', position: 'buy', strike: s, quantity: 1, premium: 0 },
            { type: 'put', position: 'buy', strike: s, quantity: 1, premium: 0 }
        ];
    } else if (preset === 'long_strangle') {
        state.strategyLegs = [
            { type: 'put', position: 'buy', strike: Math.round(s * 0.95), quantity: 1, premium: 0 },
            { type: 'call', position: 'buy', strike: Math.round(s * 1.05), quantity: 1, premium: 0 }
        ];
    } else if (preset === 'iron_condor') {
        state.strategyLegs = [
            { type: 'put', position: 'buy', strike: Math.round(s * 0.85), quantity: 1, premium: 0 },
            { type: 'put', position: 'sell', strike: Math.round(s * 0.95), quantity: 1, premium: 0 },
            { type: 'call', position: 'sell', strike: Math.round(s * 1.05), quantity: 1, premium: 0 },
            { type: 'call', position: 'buy', strike: Math.round(s * 1.15), quantity: 1, premium: 0 }
        ];
    }
    renderStrategyLegsTable();
    updateStrategyPayoff();
}

function renderStrategyLegsTable() {
    const tbody = document.getElementById('strategy-legs-tbody');
    tbody.innerHTML = '';

    state.strategyLegs.forEach((leg, idx) => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-800/40';
        tr.innerHTML = `
            <td class="p-2">
                <select onchange="updateLegField(${idx}, 'type', this.value)" class="bg-gray-800 border border-gray-700 text-gray-200 rounded px-2 py-1">
                    <option value="call" ${leg.type === 'call' ? 'selected' : ''}>Call</option>
                    <option value="put" ${leg.type === 'put' ? 'selected' : ''}>Put</option>
                    <option value="stock" ${leg.type === 'stock' ? 'selected' : ''}>Stock (Underlying)</option>
                </select>
            </td>
            <td class="p-2">
                <select onchange="updateLegField(${idx}, 'position', this.value)" class="bg-gray-800 border border-gray-700 text-gray-200 rounded px-2 py-1">
                    <option value="buy" ${leg.position === 'buy' ? 'selected' : ''}>Buy (+Long)</option>
                    <option value="sell" ${leg.position === 'sell' ? 'selected' : ''}>Sell (-Short)</option>
                </select>
            </td>
            <td class="p-2">
                <input type="number" step="1" value="${leg.strike}" onchange="updateLegField(${idx}, 'strike', parseFloat(this.value))" class="w-20 bg-gray-800 border border-gray-700 text-cyan-300 rounded px-2 py-1 font-mono">
            </td>
            <td class="p-2">
                <input type="number" step="1" min="1" value="${leg.quantity}" onchange="updateLegField(${idx}, 'quantity', parseInt(this.value))" class="w-16 bg-gray-800 border border-gray-700 text-gray-200 rounded px-2 py-1 font-mono">
            </td>
            <td class="p-2 text-gray-400 font-mono">
                Auto Black-Scholes
            </td>
            <td class="p-2 text-right">
                <button onclick="removeStrategyLeg(${idx})" class="text-rose-400 hover:text-rose-300 px-2 py-1">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function updateLegField(idx, field, value) {
    state.strategyLegs[idx][field] = value;
    updateStrategyPayoff();
}

function addStrategyLeg() {
    state.strategyLegs.push({
        type: 'call',
        position: 'buy',
        strike: state.S,
        quantity: 1,
        premium: 0
    });
    renderStrategyLegsTable();
    updateStrategyPayoff();
}

function removeStrategyLeg(idx) {
    if (state.strategyLegs.length > 1) {
        state.strategyLegs.splice(idx, 1);
        renderStrategyLegsTable();
        updateStrategyPayoff();
    } else {
        alert('Portfolio must have at least 1 leg.');
    }
}

async function updateStrategyPayoff() {
    if (!chartStrategy) return;

    try {
        const res = await fetch('/api/strategy_payoff', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                legs: state.strategyLegs,
                S: state.S,
                r: state.r,
                sigma: state.sigma,
                T: state.T,
                q: state.q
            })
        });

        const data = await res.json();

        // Update Strategy Summary KPI
        document.getElementById('strat-cost').textContent = `$${data.total_entry_cost.toFixed(2)}`;
        document.getElementById('strat-max-profit').textContent = typeof data.max_profit === 'number' ? `$${data.max_profit.toFixed(2)}` : data.max_profit;
        document.getElementById('strat-max-loss').textContent = typeof data.max_loss === 'number' ? `$${data.max_loss.toFixed(2)}` : data.max_loss;
        document.getElementById('strat-breakevens').textContent = data.breakevens.length > 0 ? data.breakevens.map(b => `$${b}`).join(', ') : 'None';

        // Update Strategy Chart
        chartStrategy.data.labels = data.spots.map(s => `$${s.toFixed(1)}`);
        chartStrategy.data.datasets = [
            {
                label: 'PnL at Expiry',
                data: data.payoffs_expiry,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.08)',
                borderWidth: 2.5,
                fill: true,
                pointRadius: 0
            },
            {
                label: 'Current Black-Scholes PnL (T > 0)',
                data: data.payoffs_current,
                borderColor: '#818cf8',
                borderWidth: 2,
                borderDash: [4, 4],
                fill: false,
                pointRadius: 0
            }
        ];
        chartStrategy.update();
    } catch (err) {
        console.error('Strategy payoff error:', err);
    }
}

// -------------------------------------------------------------
// Option Chain Matrix
// -------------------------------------------------------------
let chainDataCache = null;

async function updateOptionChain() {
    const url = `/api/option_chain?S=${state.S}&r=${state.r}&sigma=${state.sigma}&T=${state.T}&q=${state.q}&strikes=17`;
    try {
        const res = await fetch(url);
        const data = await res.json();
        chainDataCache = data;

        document.getElementById('chain-spot-ref').textContent = `$${data.spot.toFixed(2)}`;
        const tbody = document.getElementById('option-chain-tbody');
        tbody.innerHTML = '';

        data.chain.forEach(row => {
            const tr = document.createElement('tr');
            if (row.is_atm) tr.className = 'atm-row border-y border-indigo-500/50';

            const callBg = row.call_itm ? 'bg-emerald-950/20 text-emerald-300 font-semibold' : 'text-gray-300';
            const putBg = row.put_itm ? 'bg-rose-950/20 text-rose-300 font-semibold' : 'text-gray-300';

            tr.innerHTML = `
                <td class="p-2.5 ${callBg}">$${row.call_price.toFixed(2)}</td>
                <td class="p-2.5 text-gray-400">${row.call_delta.toFixed(3)}</td>
                <td class="p-2.5 text-purple-400">$${row.call_theta.toFixed(3)}</td>
                <td class="p-2.5 text-gray-400 border-r border-gray-700">${row.gamma.toFixed(4)}</td>
                <td class="p-2.5 bg-gray-800/90 font-bold text-cyan-300 border-r border-gray-700">$${row.strike.toFixed(1)}</td>
                <td class="p-2.5 text-gray-400 border-r border-gray-800">${row.gamma.toFixed(4)}</td>
                <td class="p-2.5 text-purple-400">$${row.put_theta.toFixed(3)}</td>
                <td class="p-2.5 text-gray-400">${row.put_delta.toFixed(3)}</td>
                <td class="p-2.5 ${putBg}">$${row.put_price.toFixed(2)}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error('Option chain error:', err);
    }
}

function exportChainCSV() {
    if (!chainDataCache) return;
    let csv = "Call Price,Call Delta,Call Theta/Day,Gamma,Strike,Put Theta/Day,Put Delta,Put Price\n";
    chainDataCache.chain.forEach(r => {
        csv += `${r.call_price},${r.call_delta},${r.call_theta},${r.gamma},${r.strike},${r.put_theta},${r.put_delta},${r.put_price}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `black_scholes_option_chain_S${state.S}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}

// -------------------------------------------------------------
// Tab Switching & Modal Handling
// -------------------------------------------------------------
function switchTab(tabId) {
    state.activeTab = tabId;
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));

    document.getElementById(tabId).classList.remove('hidden');
    const btn = document.getElementById(`btn-${tabId}`);
    if (btn) btn.classList.add('active');

    // Trigger tab-specific renders
    if (tabId === 'tab-payoff') renderPayoffChart();
    if (tabId === 'tab-greeks') renderGreeksChart();
    if (tabId === 'tab-heatmap') renderHeatmap();
    if (tabId === 'tab-surface') renderSurface();
    if (tabId === 'tab-strategy') {
        renderStrategyLegsTable();
        updateStrategyPayoff();
    }
    if (tabId === 'tab-chain') updateOptionChain();
}

function openModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.remove('hidden');
        renderMath();
    }
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
}
