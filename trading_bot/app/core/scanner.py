import datetime
from app.services.tinkoff_service import TinkoffService
from app.services.backtester import Backtester
import pandas as pd
import time

class MarketScanner:
    def __init__(self, token: str):
        self.client = TinkoffService(token=token, sandbox=True)
        
    def scan_and_select_top_assets(self, max_assets: int = 20, max_lot_price: float = 500.0) -> list:
        print("Fetching all shares...")
        try:
            shares = self.client.get_shares()
        except Exception as e:
            print(f"Error fetching shares: {e}")
            return []
            
        filtered_shares = []
        for s in shares:
            if s.get("currency") != "rub":
                continue
            filtered_shares.append(s)
            
        print(f"Found {len(filtered_shares)} RUB shares. Returning initial list for background processing.")
        
        results = []
        for share in filtered_shares[:10]: 
            figi = share['figi']
            ticker = share['ticker']
            lot = share.get("lot", 1)
            name = share.get("name", "")
            
            results.append({
                "figi": figi,
                "ticker": ticker,
                "name": name,
                "lot": lot,
                "current_price": 0,
                "lot_price": 0,
                "best_strategy": "Pending...",
                "expected_return": 0,
                "active": False,
                "max_lots": 1,
                "max_trades": 1,
                "sparkline": [],
                "status": "PENDING"
            })
                
        return results[:max_assets]
