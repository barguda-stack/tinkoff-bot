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
        response = requests.post(url, headers=self.headers, json=payload or {}, verify=False)
        response.raise_for_status()
        return response.json()

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
        payload = {
            "figi": figi,
            "from": from_time.isoformat() + "Z",
            "to": to_time.isoformat() + "Z",
            "interval": "CANDLE_INTERVAL_5_MIN"
        }
        data = self._post("tinkoff.public.invest.api.contract.v1.MarketDataService/GetCandles", payload)
        candles = data.get("candles", [])
        
        if not candles:
            return pd.DataFrame()
            
        df = pd.DataFrame(candles)
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
