import datetime
from app.services.tinkoff_service import TinkoffService
from app.services.backtester import Backtester
import pandas as pd
import time

class MarketScanner:
    def __init__(self, token: str):
        self.client = TinkoffService(token=token)
        
    def scan_and_select_top_assets(self, max_assets: int = 20, max_lot_price: float = 500.0) -> list:
        """
        Scans all shares, filters by lot price, backtests over the last year,
        and selects top `max_assets` best performing instruments.
        """
        print("Fetching all shares...")
        try:
            shares = self.client.get_shares()
        except Exception as e:
            print(f"Error fetching shares: {e}")
            return []
            
        filtered_shares = []
        for s in shares:
            # We only want RUB shares for Moex usually
            if s.get("currency") != "rub":
                continue
                
            lot = s.get("lot", 1)
            # Rough estimation: we'd need current price to know lot price exactly.
            # To avoid doing thousands of API calls, we'll fetch historical data for 
            # a smaller subset or just fetch history and filter afterwards.
            filtered_shares.append(s)
            
        print(f"Found {len(filtered_shares)} RUB shares. Backtesting top candidates...")
        
        # In a real scenario, we might want to pre-filter by liquidity/volume.
        # Here we just iterate (taking a subset for demo/speed purposes).
        # We will take up to 50 assets to backtest to not hit API limits too hard during init.
        
        results = []
        now = datetime.datetime.utcnow()
        one_year_ago = now - datetime.timedelta(days=365)
        
        for share in filtered_shares[:50]: # Limit for demo, remove limit in prod with rate handling
            figi = share['figi']
            ticker = share['ticker']
            lot = share.get("lot", 1)
            name = share.get("name", "")
            
            try:
                df = self.client.get_historical_candles(figi, one_year_ago, now)
                if df.empty:
                    continue
                    
                current_price = df['close'].iloc[-1]
                lot_price = current_price * lot
                
                # Filter by lot price (default < 500 enabled)
                if lot_price > max_lot_price:
                    continue
                    
                tester = Backtester(df)
                best_strat = tester.get_best_strategy()
                
                if best_strat['return'] > 0: # Only consider profitable ones
                    results.append({
                        "figi": figi,
                        "ticker": ticker,
                        "name": name,
                        "lot": lot,
                        "current_price": current_price,
                        "lot_price": lot_price,
                        "best_strategy": best_strat['name'],
                        "expected_return": best_strat['return'],
                        "active": True # Auto-activate if < 500 (already filtered)
                    })
                
                # sleep slightly to avoid rate limit
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Failed to process {ticker}: {e}")
                
        # Sort by expected return descending
        results.sort(key=lambda x: x['expected_return'], reverse=True)
        return results[:max_assets]
