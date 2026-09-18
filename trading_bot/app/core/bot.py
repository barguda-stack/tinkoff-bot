import os
import datetime
from typing import List, Dict
import threading
import time
from app.core.scanner import MarketScanner
from app.services.tinkoff_service import TinkoffService

class TradingBot:
    def __init__(self):
        self.token = os.getenv("TINKOFF_TOKEN") or "t.Eys4FUpVirKiksOSslAZPCw_WLiLNA79T5KFBzZGRTKq2Pxsbs0ba8pWDj9mN7rnCT4EMkeHV09rRIM55u5kqw"
        # SANDBOX DEFAULT = True
        self.client = TinkoffService(token=self.token, sandbox=True)
        self.scanner = MarketScanner(token=self.token)
        self.selected_assets: List[Dict] = []
        self.is_running = False
        self.last_scan_time = None
        
        self.portfolio_stats = {
            "balance": 100000.0,
            "total_profit": 0.0
        }
        self.commission_rate = 0.003
        self.position_sizing_pct = 0.10 # 10%

        # Active positions: { "FIGI": {"ticker": "SBER", "buy_price": 100.0, "qty": 10, "max_trades": 1, "trades_done": 1} }
        self.active_positions = {}

    def fetch_commission_rate(self):
        try:
            self.commission_rate = 0.003
            print(f"Set commission rate to {self.commission_rate * 100}%")
        except Exception as e:
            print(f"Error fetching commission: {e}")

    def start(self):
        self.fetch_commission_rate()
        # Initialize Sandbox account and fetch balance
        try:
            acc_id = self.client.get_accounts()
            print(f"Connected to account: {acc_id}")
        except Exception as e:
            print(f"Could not init account: {e}")
            
        self.is_running = True
        print("Bot started.")
        threading.Thread(target=self._run_scan).start()

    def stop(self):
        self.is_running = False
        print("Bot stopped.")

    def _run_scan(self):
        if not self.is_running:
            return
            
        print("Starting market scan to find candidate assets...")
        try:
            self.selected_assets = self.scanner.scan_and_select_top_assets(max_assets=10, max_lot_price=500.0)
            self.last_scan_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Found {len(self.selected_assets)} initial candidates. Starting background backtesting...")
            
            # Start background backtesting for each asset
            threading.Thread(target=self._background_backtest, daemon=True).start()
            
        except Exception as e:
            print(f"Scan failed: {e}")

    def _background_backtest(self):
        from app.services.backtester import Backtester
        
        now = datetime.datetime.utcnow()
        one_year_ago = now - datetime.timedelta(days=365)
        
        for asset in self.selected_assets:
            if not self.is_running:
                break
                
            asset["status"] = "DOWNLOADING"
            print(f"[{asset['ticker']}] Status: DOWNLOADING (Fetching 1 year of history)...")
            
            try:
                df = self.client.get_historical_candles(asset['figi'], one_year_ago, now)
                
                if df.empty:
                    asset["status"] = "ERROR: No data"
                    continue
                
                asset["status"] = "BACKTESTING"
                print(f"[{asset['ticker']}] Status: BACKTESTING...")
                
                current_price = df['close'].iloc[-1]
                lot_price = current_price * asset['lot']
                
                tester = Backtester(df)
                best_strat = tester.get_best_strategy()
                
                asset["current_price"] = current_price
                asset["lot_price"] = lot_price
                asset["best_strategy"] = best_strat['name']
                asset["expected_return"] = best_strat['return']
                asset["sparkline"] = df['close'].tail(50).tolist()
                
                is_active = True
                if lot_price > 500.0:
                    is_active = False
                
                asset["active"] = is_active
                asset["status"] = "READY"
                print(f"[{asset['ticker']}] Status: READY. Strategy: {best_strat['name']}")
                
            except Exception as e:
                asset["status"] = "ERROR"
                print(f"[{asset['ticker']}] Failed during backtest: {e}")
                
        print("Background backtesting complete for all assets.")

    def execute_trade(self, figi: str, ticker: str, direction: str, quantity: int):
        try:
            res = self.client.place_market_order(figi, quantity, direction)
            print(f"Successfully executed {direction} for {quantity} lots of {ticker}. OrderID: {res.get('orderId')}")
            return res
        except Exception as e:
            print(f"Failed to execute trade for {ticker}: {e}")
            return None

bot_instance = TradingBot()
