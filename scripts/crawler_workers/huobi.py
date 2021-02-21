import base64
import hashlib
import hmac
import urllib
from datetime import datetime

import ccxt
import pandas as pd
import requests
from utils import retry_getter


def create_signature(
    api_key: str,
    method: str,
    host: str,
    path: str,
    secret_key: str
):
    sorted_params = [
        ("AccessKeyId", api_key),
        ("SignatureMethod", "HmacSHA256"),
        ("SignatureVersion", "2"),
        ("Timestamp", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
    ]
    encode_params = urllib.parse.urlencode(sorted_params)

    payload = [method, host, path, encode_params]
    payload = "\n".join(payload)
    payload = payload.encode(encoding="UTF8")

    secret_key = secret_key.encode(encoding="UTF8")

    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)

    params = dict(sorted_params)
    params["Signature"] = signature.decode("UTF8")
    return params


def get_swap_account(secret):
    api_path = '/swap-api/v1/swap_account_info'
    api_host = 'api.hbdm.com'
    url = f'https://{api_host}{api_path}'
    params=create_signature(secret['apiKey'], 'POST', api_host, api_path, secret['secret'])
    resp = retry_getter(lambda: requests.post(url, params=params), 10)
    df = pd.DataFrame(resp.json()['data'])
    df = df[df['margin_balance'] > 0]
    df['type'] = 'swap'
    df.rename(columns={
        'symbol': 'currency',
        'contract_code': 'underlying',
        'margin_balance': 'equity',
        'risk_rate': 'margin_ratio'
    }, inplace=True)
    return df[['type', 'currency', 'underlying', 'equity', 'margin_ratio']]

def get_account(secret):
    exg = ccxt.huobipro(secret)
    accounts = retry_getter(exg.private_get_account_accounts, 1)['data']
    dfs = []
    for acc in accounts:
        if acc['type'] in ['spot', 'crypto-loans']:
            data = retry_getter(lambda: exg.private_get_account_accounts_id_balance({'id': acc['id']}), 1)
            df = pd.DataFrame(data['data']['list'])
            df['balance'] = df['balance'].astype('float')
            dfs.append(df)
    df_spot = pd.concat(dfs)
    df_spot = df_spot[df_spot['balance'].abs() > 0].groupby('currency', as_index=False)[['balance']].sum()
    df_spot['currency'] = df_spot['currency'].str.upper()
    return df_spot, get_swap_account(secret), \
        pd.DataFrame(columns=['instrument_id', 'last', 'qty', 'avg_cost', 'pnl_ratio', 'pnl'])
