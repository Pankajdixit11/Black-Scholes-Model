"""
Black-Scholes Standalone Web Server
Powered by Python's built-in http.server and unmodified code.py
"""

import http.server
import json
import math
import os
import sys
import urllib.parse
from typing import Dict, Any, List

# Load BS functions from bs_engine_loader
import bs_engine_loader as bs

PORT = 8000
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

class BlackScholesRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        # Add CORS and Cache-Control headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, data: Dict[str, Any], status: int = 200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        def default_encoder(obj):
            if hasattr(obj, 'item'):
                return obj.item()
            if hasattr(obj, 'tolist'):
                return obj.tolist()
            return str(obj)

        self.wfile.write(json.dumps(data, default=default_encoder).encode('utf-8'))

    def _parse_query(self) -> Dict[str, str]:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        return {k: v[0] for k, v in params.items()}

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode('utf-8')
        return json.loads(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path == "/api/calculate":
                self.handle_calculate()
            elif path == "/api/curves":
                self.handle_curves()
            elif path == "/api/heatmap":
                self.handle_heatmap()
            elif path == "/api/surface":
                self.handle_surface()
            elif path == "/api/option_chain":
                self.handle_option_chain()
            elif path == "/api/status":
                self._send_json({"status": "ok", "message": "Black-Scholes API running with unmodified code.py"})
            else:
                # Serve static files
                if path == "/" or path == "":
                    self.path = "/index.html"
                super().do_GET()
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            if path == "/api/implied_vol":
                self.handle_implied_vol()
            elif path == "/api/strategy_payoff":
                self.handle_strategy_payoff()
            else:
                self._send_json({"error": "Endpoint not found"}, status=404)
        except Exception as e:
            self._send_json({"error": str(e)}, status=500)

    # ------------------- API Handlers -------------------

    def handle_calculate(self):
        q = self._parse_query()
        S = float(q.get("S", 100.0))
        K = float(q.get("K", 100.0))
        r = float(q.get("r", 0.05))
        sigma = float(q.get("sigma", 0.20))
        T = float(q.get("T", 1.0))
        div = float(q.get("q", 0.0))

        result = bs.calculate_all(S, K, r, sigma, T, div)
        # Convert numpy floats to standard Python floats for JSON serialization
        greeks_clean = {k: float(v) for k, v in result["greeks"].items()}
        result["greeks"] = greeks_clean
        self._send_json(result)

    def handle_curves(self):
        q = self._parse_query()
        S = float(q.get("S", 100.0))
        K = float(q.get("K", 100.0))
        r = float(q.get("r", 0.05))
        sigma = float(q.get("sigma", 0.20))
        T = float(q.get("T", 1.0))
        div = float(q.get("q", 0.0))

        # Spot range: 50% to 150% of K
        s_min = max(1.0, K * 0.4)
        s_max = K * 1.6
        num_points = 80
        step = (s_max - s_min) / (num_points - 1)
        spots = [s_min + i * step for i in range(num_points)]

        call_prices = []
        put_prices = []
        call_payoffs = []
        put_payoffs = []
        delta_calls = []
        delta_puts = []
        gammas = []
        vegas = []
        theta_calls = []
        theta_puts = []
        rho_calls = []
        rho_puts = []

        current_call = bs.bs_call(S, K, r, sigma, T, div)
        current_put = bs.bs_put(S, K, r, sigma, T, div)

        for s_val in spots:
            cp = bs.bs_call(s_val, K, r, sigma, T, div)
            pp = bs.bs_put(s_val, K, r, sigma, T, div)
            call_prices.append(cp)
            put_prices.append(pp)
            call_payoffs.append(max(0.0, s_val - K) - current_call)
            put_payoffs.append(max(0.0, K - s_val) - current_put)

            grk = bs.greeks(s_val, K, r, sigma, T, div)
            delta_calls.append(float(grk["Delta(Call)"]))
            delta_puts.append(float(grk["Delta(Put)"]))
            gammas.append(float(grk["Gamma"]))
            vegas.append(float(grk["Vega"]))
            theta_calls.append(float(grk["Theta(Call)"]))
            theta_puts.append(float(grk["Theta(Put)"]))
            rho_calls.append(float(grk["Rho(Call)"]))
            rho_puts.append(float(grk["Rho(Put)"]))

        # Time Decay Curves (T from 0.01 to 2.0 or current T)
        t_max = max(1.0, T * 1.5)
        t_points = 60
        t_step = (t_max - 0.005) / (t_points - 1)
        times = [0.005 + i * t_step for i in range(t_points)]
        time_call_prices = [bs.bs_call(S, K, r, sigma, t, div) for t in times]
        time_put_prices = [bs.bs_put(S, K, r, sigma, t, div) for t in times]
        time_thetas = [float(bs.greeks(S, K, r, sigma, t, div)["Theta(Call)"]) for t in times]

        self._send_json({
            "spots": spots,
            "call_prices": call_prices,
            "put_prices": put_prices,
            "call_payoffs": call_payoffs,
            "put_payoffs": put_payoffs,
            "delta_calls": delta_calls,
            "delta_puts": delta_puts,
            "gammas": gammas,
            "vegas": vegas,
            "theta_calls": theta_calls,
            "theta_puts": theta_puts,
            "rho_calls": rho_calls,
            "rho_puts": rho_puts,
            "times": times,
            "time_call_prices": time_call_prices,
            "time_put_prices": time_put_prices,
            "time_thetas": time_thetas
        })

    def handle_heatmap(self):
        q = self._parse_query()
        S = float(q.get("S", 100.0))
        K = float(q.get("K", 100.0))
        r = float(q.get("r", 0.05))
        sigma = float(q.get("sigma", 0.20))
        T = float(q.get("T", 1.0))
        div = float(q.get("q", 0.0))

        # Spot grid (+- 30%)
        num_s = 15
        s_min = S * 0.7
        s_max = S * 1.3
        s_step = (s_max - s_min) / (num_s - 1)
        spots = [round(s_min + i * s_step, 2) for i in range(num_s)]

        # Vol grid (10% to 80%)
        num_v = 12
        v_min = max(0.05, sigma * 0.4)
        v_max = min(1.2, sigma * 2.2)
        v_step = (v_max - v_min) / (num_v - 1)
        vols = [round(v_min + i * v_step, 3) for i in range(num_v)]

        call_matrix = []
        put_matrix = []
        call_delta_matrix = []
        gamma_matrix = []
        vega_matrix = []

        for v in vols:
            call_row = []
            put_row = []
            delta_row = []
            gamma_row = []
            vega_row = []
            for s in spots:
                c = bs.bs_call(s, K, r, v, T, div)
                p = bs.bs_put(s, K, r, v, T, div)
                grk = bs.greeks(s, K, r, v, T, div)
                call_row.append(round(c, 2))
                put_row.append(round(p, 2))
                delta_row.append(round(float(grk["Delta(Call)"]), 3))
                gamma_row.append(round(float(grk["Gamma"]), 4))
                vega_row.append(round(float(grk["Vega"]), 2))
            call_matrix.append(call_row)
            put_matrix.append(put_row)
            call_delta_matrix.append(delta_row)
            gamma_matrix.append(gamma_row)
            vega_matrix.append(vega_row)

        self._send_json({
            "spots": spots,
            "vols": [f"{round(v*100, 1)}%" for v in vols],
            "vols_raw": vols,
            "call_matrix": call_matrix,
            "put_matrix": put_matrix,
            "call_delta_matrix": call_delta_matrix,
            "gamma_matrix": gamma_matrix,
            "vega_matrix": vega_matrix
        })

    def handle_surface(self):
        q = self._parse_query()
        S = float(q.get("S", 100.0))
        K = float(q.get("K", 100.0))
        r = float(q.get("r", 0.05))
        sigma = float(q.get("sigma", 0.20))
        div = float(q.get("q", 0.0))

        # Spot mesh & Time mesh
        spots = [round(K * (0.6 + 0.05 * i), 2) for i in range(17)] # 17 points
        times = [round(0.05 + 0.1 * i, 2) for i in range(15)]       # 15 points

        call_z = []
        put_z = []
        gamma_z = []
        vega_z = []

        for t in times:
            c_row = []
            p_row = []
            g_row = []
            v_row = []
            for s in spots:
                c_row.append(round(bs.bs_call(s, K, r, sigma, t, div), 3))
                p_row.append(round(bs.bs_put(s, K, r, sigma, t, div), 3))
                grk = bs.greeks(s, K, r, sigma, t, div)
                g_row.append(round(float(grk["Gamma"]), 5))
                v_row.append(round(float(grk["Vega"]), 3))
            call_z.append(c_row)
            put_z.append(p_row)
            gamma_z.append(g_row)
            vega_z.append(v_row)

        self._send_json({
            "spots": spots,
            "times": times,
            "call_z": call_z,
            "put_z": put_z,
            "gamma_z": gamma_z,
            "vega_z": vega_z
        })

    def handle_option_chain(self):
        q = self._parse_query()
        S = float(q.get("S", 100.0))
        r = float(q.get("r", 0.05))
        sigma = float(q.get("sigma", 0.20))
        T = float(q.get("T", 1.0))
        div = float(q.get("q", 0.0))
        num_strikes = int(q.get("strikes", 15))

        step = max(1.0, round(S * 0.02, 1))
        center_k = round(S / step) * step
        half = num_strikes // 2
        strikes = [round(center_k + (i - half) * step, 2) for i in range(num_strikes)]

        chain = []
        for k_val in strikes:
            c_price = bs.bs_call(S, k_val, r, sigma, T, div)
            p_price = bs.bs_put(S, k_val, r, sigma, T, div)
            grk = bs.greeks(S, k_val, r, sigma, T, div)
            
            c_itm = S > k_val
            p_itm = S < k_val

            chain.append({
                "strike": k_val,
                "call_price": round(c_price, 3),
                "call_delta": round(float(grk["Delta(Call)"]), 4),
                "call_theta": round(float(grk["Theta(Call)"]) / 365, 4),
                "call_itm": c_itm,
                "gamma": round(float(grk["Gamma"]), 4),
                "vega": round(float(grk["Vega"]) / 100, 4),
                "put_price": round(p_price, 3),
                "put_delta": round(float(grk["Delta(Put)"]), 4),
                "put_theta": round(float(grk["Theta(Put)"]) / 365, 4),
                "put_itm": p_itm,
                "is_atm": abs(S - k_val) < step * 0.6
            })

        self._send_json({"spot": S, "chain": chain})

    def handle_implied_vol(self):
        body = self._read_json_body()
        price = float(body.get("price", 10.0))
        S = float(body.get("S", 100.0))
        K = float(body.get("K", 100.0))
        r = float(body.get("r", 0.05))
        T = float(body.get("T", 1.0))
        opt_type = body.get("type", "call").lower()
        q = float(body.get("q", 0.0))

        # Check intrinsic lower bound
        intrinsic = max(0.0, S * math.exp(-q*T) - K * math.exp(-r*T)) if opt_type == "call" else max(0.0, K * math.exp(-r*T) - S * math.exp(-q*T))
        if price <= intrinsic:
            self._send_json({
                "error": f"Market price ({price:.2f}) must be strictly greater than discounted intrinsic value ({intrinsic:.2f}).",
                "iv": None
            }, status=400)
            return

        try:
            iv = bs.implied_volatility(price, S, K, r, T, type=opt_type, q=q)
            # Check price recovered by model
            recovered_price = bs.bs_call(S, K, r, iv, T, q) if opt_type == "call" else bs.bs_put(S, K, r, iv, T, q)
            diff = abs(price - recovered_price)

            self._send_json({
                "implied_volatility": round(iv, 6),
                "implied_volatility_pct": round(iv * 100, 3),
                "recovered_price": round(recovered_price, 4),
                "error_margin": round(diff, 6),
                "converged": diff < 1e-3
            })
        except Exception as e:
            self._send_json({"error": f"Implied volatility solver error: {str(e)}"}, status=500)

    def handle_strategy_payoff(self):
        body = self._read_json_body()
        legs = body.get("legs", [])
        S = float(body.get("S", 100.0))
        r = float(body.get("r", 0.05))
        sigma = float(body.get("sigma", 0.20))
        T = float(body.get("T", 1.0))
        q = float(body.get("q", 0.0))

        # Calculate Spot Range
        s_min = S * 0.5
        s_max = S * 1.5
        num_points = 100
        step = (s_max - s_min) / (num_points - 1)
        spots = [s_min + i * step for i in range(num_points)]

        total_entry_cost = 0.0
        portfolio_delta = 0.0
        portfolio_gamma = 0.0
        portfolio_vega = 0.0
        portfolio_theta = 0.0

        for leg in legs:
            l_type = leg.get("type", "call") # "call", "put", "stock"
            l_pos = leg.get("position", "buy") # "buy" (+1) or "sell" (-1)
            l_qty = float(leg.get("quantity", 1))
            multiplier = 1.0 if l_pos == "buy" else -1.0
            l_strike = float(leg.get("strike", S))

            if l_type == "stock":
                leg_price = S
                total_entry_cost += multiplier * l_qty * leg_price
                portfolio_delta += multiplier * l_qty
            elif l_type == "call":
                leg_price = bs.bs_call(S, l_strike, r, sigma, T, q)
                total_entry_cost += multiplier * l_qty * leg_price
                grk = bs.greeks(S, l_strike, r, sigma, T, q)
                portfolio_delta += multiplier * l_qty * float(grk["Delta(Call)"])
                portfolio_gamma += multiplier * l_qty * float(grk["Gamma"])
                portfolio_vega += multiplier * l_qty * float(grk["Vega"])
                portfolio_theta += multiplier * l_qty * float(grk["Theta(Call)"])
            elif l_type == "put":
                leg_price = bs.bs_put(S, l_strike, r, sigma, T, q)
                total_entry_cost += multiplier * l_qty * leg_price
                grk = bs.greeks(S, l_strike, r, sigma, T, q)
                portfolio_delta += multiplier * l_qty * float(grk["Delta(Put)"])
                portfolio_gamma += multiplier * l_qty * float(grk["Gamma"])
                portfolio_vega += multiplier * l_qty * float(grk["Vega"])
                portfolio_theta += multiplier * l_qty * float(grk["Theta(Put)"])

        payoffs_expiry = []
        payoffs_current = []

        for s_val in spots:
            expiry_val = 0.0
            current_val = 0.0

            for leg in legs:
                l_type = leg.get("type", "call")
                l_pos = leg.get("position", "buy")
                l_qty = float(leg.get("quantity", 1))
                multiplier = 1.0 if l_pos == "buy" else -1.0
                l_strike = float(leg.get("strike", S))

                if l_type == "stock":
                    expiry_val += multiplier * l_qty * s_val
                    current_val += multiplier * l_qty * s_val
                elif l_type == "call":
                    expiry_val += multiplier * l_qty * max(0.0, s_val - l_strike)
                    current_val += multiplier * l_qty * bs.bs_call(s_val, l_strike, r, sigma, T, q)
                elif l_type == "put":
                    expiry_val += multiplier * l_qty * max(0.0, l_strike - s_val)
                    current_val += multiplier * l_qty * bs.bs_put(s_val, l_strike, r, sigma, T, q)

            pnl_expiry = expiry_val - total_entry_cost
            pnl_current = current_val - total_entry_cost
            payoffs_expiry.append(round(pnl_expiry, 2))
            payoffs_current.append(round(pnl_current, 2))

        # Find Breakevens (zero crossings)
        breakevens = []
        for i in range(len(spots) - 1):
            if (payoffs_expiry[i] <= 0 and payoffs_expiry[i+1] > 0) or (payoffs_expiry[i] >= 0 and payoffs_expiry[i+1] < 0):
                # Linear interpolation
                x1, y1 = spots[i], payoffs_expiry[i]
                x2, y2 = spots[i+1], payoffs_expiry[i+1]
                if y2 != y1:
                    be = x1 - y1 * (x2 - x1) / (y2 - y1)
                    breakevens.append(round(be, 2))

        max_profit = max(payoffs_expiry)
        max_loss = min(payoffs_expiry)

        self._send_json({
            "spots": [round(s, 2) for s in spots],
            "payoffs_expiry": payoffs_expiry,
            "payoffs_current": payoffs_current,
            "total_entry_cost": round(total_entry_cost, 2),
            "breakevens": breakevens,
            "max_profit": "Unlimited" if max_profit > 10000 else round(max_profit, 2),
            "max_loss": "-Unlimited" if max_loss < -10000 else round(max_loss, 2),
            "portfolio_greeks": {
                "delta": round(portfolio_delta, 4),
                "gamma": round(portfolio_gamma, 5),
                "vega": round(portfolio_vega, 3),
                "theta": round(portfolio_theta, 3)
            }
        })


def run_server(port=PORT):
    import socketserver
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), BlackScholesRequestHandler) as httpd:
        print(f"🚀 Black-Scholes Dashboard server running at http://localhost:{port}")
        print(f"✨ Powered by unmodified code.py engine")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port)
