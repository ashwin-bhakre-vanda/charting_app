import json
import requests

url = 'https://www.vandatrack.com/tickers/api/'
auth_token = "9Y1REXTBBK6ADPWB"

params = {
    'tickers': ['FB','AAPL','AMZN','NFLX','GOOG','MSFT','TSLA','NVDA','AMD','BABA'],
    'saved_list': 'false',
    'from_date': '2014-01-01',
    'to_date': '2025-10-04',
    'auth_token': auth_token,
    'type': 'buy'
    #'pagination': 'true',
}

response = requests.get(url, params=params)
d = json.loads(response.text)