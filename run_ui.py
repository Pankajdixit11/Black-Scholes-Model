"""
Black-Scholes UI Launcher
Starts the interactive quantitative web application and opens it in your default browser.
"""

import os
import sys
import webbrowser
import threading
import time

def open_browser(url):
    time.sleep(1.2)
    print(f"🌐 Opening browser at {url}...")
    webbrowser.open(url)

def main():
    print("=" * 65)
    print("📈 Black-Scholes Option Pricing & Greeks Analytics UI")
    print("✨ Engine: 100% Unmodified code.py")
    print("=" * 65)

    # Check if user wants streamlit or standalone
    mode = sys.argv[1] if len(sys.argv) > 1 else "web"

    if mode == "streamlit":
        print("🚀 Starting Streamlit Analytics Application...")
        os.system("streamlit run app.py")
    else:
        port = 8000
        url = f"http://localhost:{port}"
        print(f"🚀 Starting Standalone Web Dashboard at {url}...")
        
        # Start browser thread
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()
        
        # Run server
        import server
        server.run_server(port)

if __name__ == "__main__":
    main()
