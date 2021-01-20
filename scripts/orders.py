import json
import os

import ccxt
import fire
import pandas as pd

from utils import retry_getter, update_dataframe

GRAFANA_DATA_DIR = os.getenv('GRAFANA_DATA_DIR')

def get_okex_future_orders(secret):
    exg = ccxt.okex(secret)
    df_mkt = pd.DataFrame(exg.load_markets()).T
    future_ids = df_mkt[df_mkt['futures']]['id']
    df_order_list = []
    for inst_id in future_ids:
        order_data = retry_getter(lambda: exg.futures_get_orders_instrument_id({
            'instrument_id': inst_id,
            'state': 7
        }), 2)
        df_order = pd.DataFrame(order_data['order_info'])
        df_order_list.append(df_order)
        order_data = retry_getter(lambda: exg.futures_get_orders_instrument_id({
            'instrument_id': inst_id,
            'state': 6
        }), 2)
        df_order = pd.DataFrame(order_data['order_info'])
        df_order_list.append(df_order)
    df_order = pd.concat(df_order_list)
    return df_order


def work(secret_file):
    with open(secret_file) as fin:
        secrets = json.load(fin)
    
    df_list = []
    for exchange_name, accounts in secrets.items():
        if exchange_name != 'okex':
            continue # just pass for now
        for account_name, secret in accounts.items():
            df = get_okex_future_orders(secret)
            df['exchange'] = exchange_name
            df['account'] = account_name
            df_list.append(df)
    df_futures_order = pd.concat(df_list)
    df_futures_order.drop(columns=['handicap_best_price', 'status'], inplace=True)
    for c in ['size', 'filled_qty', 'type', 'order_type', 'state']:
        df_futures_order[c] = df_futures_order[c].astype('int')
    for c in ['fee', 'price', 'price_avg', 'contract_val', 'leverage', 'pnl']:
        df_futures_order[c] = df_futures_order[c].astype('float')
    df_futures_order['timestamp'] = pd.to_datetime(df_futures_order['timestamp'])
    path = os.path.join(GRAFANA_DATA_DIR, 'futures_order.pkl.xz')
    if os.path.exists(path):
        df_ori = pd.read_pickle(path)
        df_futures_order = update_dataframe(df_ori, df_futures_order, 'order_id')
    df_futures_order = df_futures_order.sort_values('timestamp', ascending=False).reset_index(drop=True)
    df_futures_order.to_pickle(path)


if __name__ == "__main__":
    fire.Fire(work)
