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
            
        print(f"Found {len(filtered_shares)} RUB shares. Backtesting top candidates...")
        
        results = []
        now = datetime.datetime.utcnow()
        # Тинькофф API не позволяет скачивать 5-минутные свечи сразу за год одним запросом.
        # Максимум за 1 день.
        one_day_ago = now - datetime.timedelta(days=1) 
        
        for share in filtered_shares[:10]: 
            figi = share['figi']
            ticker = share['ticker']
            lot = share.get("lot", 1)
            name = share.get("name", "")
            
            try:
                df = self.client.get_historical_candles(figi, one_day_ago, now)
                if df.empty:
                    continue
                    
                current_price = df['close'].iloc[-1]
                lot_price = current_price * lot
                
                tester = Backtester(df)
                best_strat = tester.get_best_strategy()
                
                is_active = True
                if lot_price > max_lot_price:
                    is_active = False 
                    
                results.append({
                    "figi": figi,
                    "ticker": ticker,
                    "name": name,
                    "lot": lot,
                    "current_price": current_price,
                    "lot_price": lot_price,
                    "best_strategy": best_strat['name'],
                    "expected_return": best_strat['return'],
                    "active": is_active,
                    "max_lots": 1,
                    "max_trades": 1
                })
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Failed to process {ticker}: {e}")
                
        results.sort(key=lambda x: x['expected_return'], reverse=True)
        return results[:max_assets]
