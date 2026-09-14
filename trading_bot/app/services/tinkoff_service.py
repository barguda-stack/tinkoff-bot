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
            response = requests.post(url, headers=self.headers, json=payload or {}, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.SSLError as e:
            print(f"[{endpoint}] SSL Error: Your VPN, Antivirus, or network proxy is blocking the connection to Tinkoff API. Try disabling VPN or Kaspersky/DrWeb Web Shield.")
            raise e
        except Exception as e:
            print(f"[{endpoint}] Request failed: {e}")
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

    def get_shares(self) -> List[dict]:
        data = self._post("tinkoff.public.invest.api.contract.v1.InstrumentsService/Shares", {"instrumentStatus": "INSTRUMENT_STATUS_BASE"})
        return data.get("instruments", [])

    def get_historical_candles(self, figi: str, from_time: datetime, to_time: datetime) -> pd.DataFrame:
        import time
        all_candles = []
        current_time = from_time
        
        print(f"Fetching history for {figi} day by day...")
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
                print(f"Error fetching candles for {figi} from {current_time} to {next_time}: {e}")
                
            current_time = next_time
            time.sleep(0.15) # Rate limit protection

        if not all_candles:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_candles)
        def parse_quotation(q):
            if not isinstance(q, dict): return 0
            return int(q.get("units", 0)) + int(q.get("nano", 0)) / 1e9

        df['open'] = df['open'].apply(parse_quotation)
        df['close'] = df['close'].apply(parse_quotation)
        df['high'] = df['high'].apply(parse_quotation)
        df['low'] = df['low'].apply(parse_quotation)
        df['volume'] = df['volume']
        df['time'] = pd.to_datetime(df['time'])
        df.set_index('time', inplace=True)
        return df

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
