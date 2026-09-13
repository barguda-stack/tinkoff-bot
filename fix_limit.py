import urllib3
urllib3.disable_warnings()
import requests
import datetime
token = 't.Eys4FUpVirKiksOSslAZPCw_WLiLNA79T5KFBzZGRTKq2Pxsbs0ba8pWDj9mN7rnCT4EMkeHV09rRIM55u5kqw'
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
url = 'https://sandbox-invest-public-api.tinkoff.ru/rest/tinkoff.public.invest.api.contract.v1.MarketDataService/GetCandles'

now = datetime.datetime.utcnow()
one_day_ago = now - datetime.timedelta(days=1)

payload = {
    'figi': 'BBG004S681W1', # MTS for example
    'from': one_day_ago.isoformat() + 'Z',
    'to': now.isoformat() + 'Z',
    'interval': 'CANDLE_INTERVAL_5_MIN'
}
res = requests.post(url, headers=headers, json=payload, verify=False)
print(res.status_code)
# print(res.text)
