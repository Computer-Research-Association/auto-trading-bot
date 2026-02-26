import pyupbit
import os
import requests
from dotenv import load_dotenv

load_dotenv()
access = os.getenv("UPBIT_ACCESS_KEY")
secret = os.getenv("UPBIT_SECRET_KEY")
upbit = pyupbit.Upbit(access, secret)

url = "https://api.upbit.com/v1/orders"
query = {'states[]': ['done', 'cancel'], 'limit': 100, 'order_by': 'desc'}
headers = upbit._request_headers(query)

res = requests.get(url, params=query, headers=headers)
print("Status:", res.status_code)
if res.status_code == 200:
    print("Found:", len(res.json()))
    if len(res.json()) > 0:
        print("First order:", res.json()[0])
else:
    print("Error:", res.text)
