"""
Black-Scholes Engine Loader
Safely and dynamically imports the pricing functions and Greeks from the unmodified code.py file.
"""

import importlib.util
import os
import sys
from typing import Dict, Any, Callable

def find_code_file() -> str:
    """Finds the absolute path to code.py in the workspace."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "Black-Scholes", "code.py"),
        os.path.join(base_dir, "code.py"),
        os.path.join(os.getcwd(), "Black-Scholes", "code.py"),
        os.path.join(os.getcwd(), "code.py")
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    raise FileNotFoundError("Could not find code.py in the workspace.")

def load_bs_engine():
    """Dynamically loads the code.py module without modifying it."""
    code_path = find_code_file()
    spec = importlib.util.spec_from_file_location("unmodified_code_module", code_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to create module spec for {code_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Load the unmodified engine
_bs_engine = load_bs_engine()

# Expose pure functions from code.py
d1: Callable = _bs_engine.d1
d2: Callable = _bs_engine.d2
bs_call: Callable = _bs_engine.bs_call
bs_put: Callable = _bs_engine.bs_put
greeks: Callable = _bs_engine.greeks
implied_volatility: Callable = _bs_engine.implied_volatility

def calculate_all(S: float, K: float, r: float, sigma: float, T: float, q: float = 0.0) -> Dict[str, Any]:
    """
    Convenience wrapper to calculate all pricing and Greeks metrics at once.
    Ensures safe handling of boundary values.
    """
    call_price = bs_call(S, K, r, sigma, T, q)
    put_price = bs_put(S, K, r, sigma, T, q)
    grks = greeks(S, K, r, sigma, T, q)
    
    # Calculate intrinsic and time value
    intrinsic_call = max(0.0, S - K)
    time_value_call = max(0.0, call_price - intrinsic_call)
    
    intrinsic_put = max(0.0, K - S)
    time_value_put = max(0.0, put_price - intrinsic_put)
    
    # Moneyness classification
    if abs(S - K) / K < 0.015:
        moneyness_call = "ATM (At The Money)"
        moneyness_put = "ATM (At The Money)"
    elif S > K:
        moneyness_call = "ITM (In The Money)"
        moneyness_put = "OTM (Out of The Money)"
    else:
        moneyness_call = "OTM (Out of The Money)"
        moneyness_put = "ITM (In The Money)"
        
    return {
        "S": S,
        "K": K,
        "r": r,
        "sigma": sigma,
        "T": T,
        "q": q,
        "call_price": call_price,
        "put_price": put_price,
        "intrinsic_call": intrinsic_call,
        "time_value_call": time_value_call,
        "intrinsic_put": intrinsic_put,
        "time_value_put": time_value_put,
        "moneyness_call": moneyness_call,
        "moneyness_put": moneyness_put,
        "greeks": grks,
        "d1": d1(S, K, r, sigma, T, q),
        "d2": d2(S, K, r, sigma, T, q),
    }

if __name__ == "__main__":
    print("Testing BS Engine Loader...")
    res = calculate_all(100, 100, 0.05, 0.20, 1.0, 0.0)
    print(f"Call Price: {res['call_price']:.4f}")
    print(f"Put Price:  {res['put_price']:.4f}")
    print("Greeks:", res['greeks'])
    iv = implied_volatility(10.5, 100, 100, 0.05, 1.0, type="call")
    print(f"Implied Vol: {iv:.4f}")
