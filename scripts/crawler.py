import json
import os
import shutil
import time
import lzma
from collections import defaultdict
from datetime import datetime

import ccxt
import fire
import pandas as pd

from utils import retry_getter
import crawler_workers

GRAFANA_DATA_DIR = os.getenv('GRAFANA_DATA_DIR')

def get_prices():
    # Should be enough for now
    exg = ccxt.okex()
    df_ticker = pd.DataFrame(retry_getter(exg.spot_get_instruments_ticker, 1))
    df_ticker = df_ticker[df_ticker['instrument_id'].str.endswith('-USDT')]
    df_ticker['currency'] = df_ticker['instrument_id'].str.split('-').str[0]
    df_ticker.set_index('currency', inplace=True)
    df_ticker = df_ticker.append(pd.Series({'last': 1}, name='USDT'))
    df_ticker = df_ticker.append(pd.Series({'last': 1}, name='USD'))
    df_ticker['last'] = df_ticker['last'].astype('float')

    exg = ccxt.huobipro()
    df_ticker_hb = pd.DataFrame(retry_getter(exg.market_get_tickers, 1)['data'])
    df_ticker_hb = df_ticker_hb[df_ticker_hb['symbol'].str.endswith('usdt')]
    df_ticker_hb['currency'] = df_ticker_hb['symbol'].str[:-4].str.upper()
    df_ticker_hb['close'] = df_ticker_hb['close'].astype('float')
    df_ticker_hb.rename(columns={'close': 'last'}, inplace=True)
    df_ticker_hb = df_ticker_hb[['currency', 'last']].set_index('currency')

    df_ticker = pd.concat([df_ticker, df_ticker_hb]).groupby(level='currency').mean()
    return df_ticker[['last']]


def value(df_acc, df_prices):
    df_acc = df_acc.join(df_prices[['last']], on='currency')
    df_acc['last'] = pd.to_numeric(df_acc['last']).fillna(0)
    col = 'balance'
    if 'balance' not in df_acc and 'equity' in df_acc:
        col = 'equity'
    df_acc['value_usd'] = df_acc['last'] * df_acc[col]
    df_acc.drop(columns='last', inplace=True)
    return df_acc[df_acc['value_usd'] > 0.01]


def work(secret_file):
    with open(secret_file) as fin:
        secrets = json.load(fin)

    df_prices = get_prices()

    df_spot_list = []
    df_futures_list = []
    df_pos_list = []
    for exchange_name, accounts in secrets.items():
        for account_name, secret in accounts.items():
            dfs = getattr(crawler_workers, exchange_name).get_account(secret)
            for df in dfs:
                df['exchange'] = exchange_name
                df['account'] = account_name
            df_spot, df_futures, df_pos = dfs
            df_spot_list.append(df_spot)
            df_futures_list.append(df_futures)
            df_pos_list.append(df_pos)

    df_spot = pd.concat(df_spot_list).set_index(['exchange', 'account']).reset_index()
    df_spot = value(df_spot, df_prices).reset_index(drop=True)
    df_futures = pd.concat(df_futures_list).set_index(['exchange', 'account', 'type']).reset_index()
    df_futures = value(df_futures, df_prices).reset_index(drop=True)
    df_pos = pd.concat(df_pos_list).set_index(['exchange', 'account']).reset_index()

    output_dir = os.path.join(GRAFANA_DATA_DIR, f'account_{datetime.now().strftime("%Y%m%d-%H%M%S")}')
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    df_spot.to_pickle(os.path.join(output_dir, 'spot.pkl.xz'))
    df_futures.to_pickle(os.path.join(output_dir, 'futures.pkl.xz'))
    df_pos.to_pickle(os.path.join(output_dir, 'pos.pkl.xz'))


if __name__ == "__main__":
    fire.Fire(work)
