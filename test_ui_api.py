"""
Test script to verify all Black-Scholes API endpoints against unmodified code.py
"""

import threading
import time
import urllib.request
import json
import socketserver
import server

def test_api():
    port = 8765
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("", port), server.BlackScholesRequestHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    base = f"http://localhost:{port}"

    print("Testing GET /api/calculate...")
    req = urllib.request.urlopen(f"{base}/api/calculate?S=100&K=100&r=0.05&sigma=0.20&T=1.0&q=0.0")
    data = json.loads(req.read().decode())
    assert abs(data["call_price"] - 10.45058) < 1e-3, f"Call price mismatch: {data['call_price']}"
    assert abs(data["put_price"] - 5.5735) < 1e-3, f"Put price mismatch: {data['put_price']}"
    print(f"[OK] /api/calculate verified (Call: {data['call_price']:.4f}, Put: {data['put_price']:.4f})")

    print("Testing GET /api/curves...")
    req = urllib.request.urlopen(f"{base}/api/curves?S=100&K=100&r=0.05&sigma=0.20&T=1.0&q=0.0")
    data = json.loads(req.read().decode())
    assert len(data["spots"]) > 50
    assert len(data["call_prices"]) == len(data["spots"])
    print(f"[OK] /api/curves verified ({len(data['spots'])} points generated)")

    print("Testing GET /api/heatmap...")
    req = urllib.request.urlopen(f"{base}/api/heatmap?S=100&K=100&r=0.05&sigma=0.20&T=1.0&q=0.0")
    data = json.loads(req.read().decode())
    assert len(data["call_matrix"]) == len(data["vols"])
    print(f"[OK] /api/heatmap verified ({len(data['vols'])}x{len(data['spots'])} matrix)")

    print("Testing GET /api/surface...")
    req = urllib.request.urlopen(f"{base}/api/surface?S=100&K=100&r=0.05&sigma=0.20&q=0.0")
    data = json.loads(req.read().decode())
    assert len(data["call_z"]) == len(data["times"])
    print(f"[OK] /api/surface verified ({len(data['times'])}x{len(data['spots'])} mesh)")

    print("Testing GET /api/option_chain...")
    req = urllib.request.urlopen(f"{base}/api/option_chain?S=100&r=0.05&sigma=0.20&T=1.0&q=0.0&strikes=15")
    data = json.loads(req.read().decode())
    assert len(data["chain"]) == 15
    print(f"[OK] /api/option_chain verified ({len(data['chain'])} strikes)")

    print("Testing POST /api/implied_vol...")
    post_data = json.dumps({"price": 10.5, "S": 100, "K": 100, "r": 0.05, "T": 1.0, "type": "call", "q": 0.0}).encode()
    req = urllib.request.Request(f"{base}/api/implied_vol", data=post_data, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode())
    assert abs(data["implied_volatility"] - 0.2013) < 1e-2
    print(f"[OK] /api/implied_vol verified (IV: {data['implied_volatility_pct']}%)")

    print("Testing POST /api/strategy_payoff...")
    strat_body = json.dumps({
        "legs": [
            {"type": "call", "position": "buy", "strike": 95, "quantity": 1},
            {"type": "call", "position": "sell", "strike": 105, "quantity": 1}
        ],
        "S": 100, "r": 0.05, "sigma": 0.20, "T": 1.0, "q": 0.0
    }).encode()
    req = urllib.request.Request(f"{base}/api/strategy_payoff", data=strat_body, headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode())
    assert len(data["payoffs_expiry"]) > 0
    print(f"[OK] /api/strategy_payoff verified (Bull Call Spread Cost: ${data['total_entry_cost']:.2f}, Max Profit: ${data['max_profit']})")

    print("Testing GET / (Static index.html)...")
    req = urllib.request.urlopen(f"{base}/")
    html_content = req.read().decode()
    assert "<title>" in html_content
    print("[OK] Static index.html served successfully")

    httpd.shutdown()
    print("\n=== ALL TESTS PASSED SUCCESSFULLY! The UI backend and engine are 100% operational ===")

if __name__ == "__main__":
    test_api()
