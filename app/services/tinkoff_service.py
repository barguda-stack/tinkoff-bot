import os
import requests
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta

# We will use direct REST API requests if SDK is unstable, 
# or standard requests wrapper for Tinkoff Invest OpenAPI v1/v2.
# Using v2 REST API directly is often more reliable than unmaintained pip packages.

class TinkoffService:
    def __init__(self, token: str = None, sandbox: bool = False):
        self.token = token or os.getenv("TINKOFF_TOKEN")
        self.sandbox = sandbox
        self.base_url = "https://invest-public-api.tinkoff.ru/rest"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _post(self, endpoint: str, payload: dict = None) -> dict:
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, headers=self.headers, json=payload or {})
        response.raise_for_status()
        return response.json()

    def get_shares(self) -> List[dict]:
        """Fetch all shares to filter out best ones."""
        data = self._post("tinkoff.public.invest.api.contract.v1.InstrumentsService/Shares", {"instrumentStatus": "INSTRUMENT_STATUS_BASE"})
        return data.get("instruments", [])

    def get_historical_candles(self, figi: str, from_time: datetime, to_time: datetime) -> pd.DataFrame:
        """Fetch historical 1-day candles for backtesting."""
        payload = {
            "figi": figi,
            "from": from_time.isoformat() + "Z",
            "to": to_time.isoformat() + "Z",
            "interval": "CANDLE_INTERVAL_DAY"
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

