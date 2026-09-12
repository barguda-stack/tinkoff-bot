import os
import datetime
from typing import List, Dict
import threading
from app.core.scanner import MarketScanner

class TradingBot:
    def __init__(self):
        self.token = os.getenv("TINKOFF_TOKEN") or "YOUR_TEST_TOKEN_HERE"
        self.scanner = MarketScanner(token=self.token)
        self.selected_assets: List[Dict] = []
        self.is_running = False
        self.last_scan_time = None
        self.portfolio_stats = {
            "balance": 100000.0, # Mock balance
            "total_profit": 0.0
        }
        
    def start(self):
        self.is_running = True
        print("Bot started.")
        # Run first scan in a separate thread to not block startup
        threading.Thread(target=self._run_scan).start()

    def stop(self):
        self.is_running = False
        print("Bot stopped.")

    def _run_scan(self):
        if not self.is_running:
            return
            
        print("Starting market scan to select top strategies and assets...")
        try:
            # Re-evaluate top 20 assets
            self.selected_assets = self.scanner.scan_and_select_top_assets(max_assets=20, max_lot_price=500.0)
            self.last_scan_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Scan complete. Selected {len(self.selected_assets)} assets.")
        except Exception as e:
            print(f"Scan failed: {e}")

bot_instance = TradingBot()
