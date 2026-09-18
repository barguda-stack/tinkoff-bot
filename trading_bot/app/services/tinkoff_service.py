import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os
import requests
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid

class TinkoffService:
    def __init__(self, token: str = None, sandbox: bool = True):
        self.token = token or os.getenv("TINKOFF_TOKEN", "t.Eys4FUpVirKiksOSslAZPCw_WLiLNA79T5KFBzZGRTKq2Pxsbs0ba8pWDj9mN7rnCT4EMkeHV09rRIM55u5kqw")
        self.sandbox = sandbox
        if self.sandbox:
            self.base_url = "https://sandbox-invest-public-api.tinkoff.ru/rest"
        else:
            self.base_url = "https://invest-public-api.tinkoff.ru/rest"
            
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.account_id = None

    def _post(self, endpoint: str, payload: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.post(url, headers=self.headers, json=payload or {}, verify=False, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"[{endpoint}] Ошибка HTTP: {e}")
            if e.response is not None:
                print(f"Ответ сервера: {e.response.text}")
            raise e
        except requests.exceptions.SSLError as e:
            print(f"[{endpoint}] Ошибка SSL: Ваш VPN, Антивирус или прокси блокирует соединение с Tinkoff API. Отключите VPN или Веб-экран Касперского.")
            raise e
        except Exception as e:
            print(f"[{endpoint}] Ошибка запроса: {e}")
            raise e

    def get_accounts(self) -> str:
        if self.sandbox:
            # For sandbox we might need to open an account first if none exists
            res = self._post("tinkoff.public.invest.api.contract.v1.SandboxService/GetSandboxAccounts")
            accounts = res.get("accounts", [])
            if not accounts:
                res = self._post("tinkoff.public.invest.api.contract.v1.SandboxService/OpenSandboxAccount")
                return res.get("accountId", "")
            return accounts[0]["id"]
        else:
            res = self._post("tinkoff.public.invest.api.contract.v1.UsersService/GetAccounts")
            accounts = res.get("accounts", [])
            if accounts:
                return accounts[0]["id"]
        return ""

    def top_up_sandbox(self, amount: int = 100000):
        if not self.sandbox:
            return False
        if not self.account_id:
            self.account_id = self.get_accounts()
        payload = {
            "accountId": self.account_id,
            "amount": {
                "currency": "rub",
                "units": str(amount),
                "nano": 0
            }
        }
        return self._post("tinkoff.public.invest.api.contract.v1.SandboxService/SandboxPayIn", payload)

    def get_shares(self) -> List[dict]:
        data = self._post("tinkoff.public.invest.api.contract.v1.InstrumentsService/Shares", {"instrumentStatus": "INSTRUMENT_STATUS_BASE"})
        return data.get("instruments", [])

    def get_historical_candles(self, figi: str, from_time: datetime, to_time: datetime) -> pd.DataFrame:
        import time
        
        # Cache mechanism
        cache_dir = "cache"
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{figi}.csv")
        
        df_cached = pd.DataFrame()
        fetch_from = from_time
        
        def parse_quotation(q):
            if not isinstance(q, dict): return 0
            return int(q.get("units", 0)) + int(q.get("nano", 0)) / 1e9
            
        if os.path.exists(cache_file):
            try:
                df_cached = pd.read_csv(cache_file, parse_dates=['time'], index_col='time')
                if not df_cached.empty:
                    last_cached_time = df_cached.index.max().tz_localize(None)
                    if last_cached_time > fetch_from:
                        fetch_from = last_cached_time + timedelta(minutes=5)
            except Exception as e:
                print(f"Ошибка чтения кэша для {figi}: {e}")
                df_cached = pd.DataFrame()

        all_candles = []
        current_time = fetch_from
        
        if current_time < to_time:
            print(f"[{figi}] Скачивание новой истории с {current_time.strftime('%Y-%m-%d')} по {to_time.strftime('%Y-%m-%d')}...")
            while current_time < to_time:
                next_time = current_time + timedelta(days=1)
                if next_time > to_time:
                    next_time = to_time
                    
                payload = {
                    "figi": figi,
                    "from": current_time.isoformat() + "Z",
                    "to": next_time.isoformat() + "Z",
                    "interval": "CANDLE_INTERVAL_5_MIN"
                }
                
                try:
                    data = self._post("tinkoff.public.invest.api.contract.v1.MarketDataService/GetCandles", payload)
                    candles = data.get("candles", [])
                    if candles:
                        all_candles.extend(candles)
                except Exception as e:
                    print(f"Ошибка скачивания свечей для {figi} с {current_time} по {next_time}: {e}")
                    
                current_time = next_time
                time.sleep(0.15)

        df_new = pd.DataFrame()
        if all_candles:
            df_new = pd.DataFrame(all_candles)
            df_new['open'] = df_new['open'].apply(parse_quotation)
            df_new['close'] = df_new['close'].apply(parse_quotation)
            df_new['high'] = df_new['high'].apply(parse_quotation)
            df_new['low'] = df_new['low'].apply(parse_quotation)
            df_new['volume'] = df_new['volume']
            df_new['time'] = pd.to_datetime(df_new['time']).dt.tz_localize(None)
            df_new.set_index('time', inplace=True)
            
        if not df_cached.empty and not df_new.empty:
            df_final = pd.concat([df_cached, df_new])
            df_final = df_final[~df_final.index.duplicated(keep='last')]
        elif not df_new.empty:
            df_final = df_new
        else:
            df_final = df_cached
            
        if not df_final.empty:
            df_final.sort_index(inplace=True)
            # Save updated cache
            try:
                df_final.to_csv(cache_file)
            except Exception as e:
                print(f"Ошибка записи кэша для {figi}: {e}")
                
        return df_final

    def place_market_order(self, figi: str, quantity: int, direction: str):
        if not self.account_id:
            self.account_id = self.get_accounts()
            
        payload = {
            "figi": figi,
            "quantity": str(quantity),
            "direction": "ORDER_DIRECTION_BUY" if direction.upper() == "BUY" else "ORDER_DIRECTION_SELL",
            "accountId": self.account_id,
            "orderType": "ORDER_TYPE_MARKET",
            "orderId": str(uuid.uuid4())
        }
        endpoint = "tinkoff.public.invest.api.contract.v1.SandboxService/PostSandboxOrder" if self.sandbox else "tinkoff.public.invest.api.contract.v1.OrdersService/PostOrder"
        return self._post(endpoint, payload)
