import os
import glob
from datetime import datetime

import pandas as pd
import utils

GRAFANA_DATA_DIR = os.getenv('GRAFANA_DATA_DIR')


def last_time():
    dir_paths = glob.glob(os.path.join(GRAFANA_DATA_DIR, 'account_*'))
    dt = os.path.basename(max(dir_paths)).split('_')[-1]
    dt = datetime.strptime(dt, '%Y%m%d-%H%M%S')
    return {"columns": [{'text': 'datetime'}], "rows": [[str(dt)]], "type": "table"}


def _get_latest():
    dir_paths = glob.glob(os.path.join(GRAFANA_DATA_DIR, 'account_*'))
    latest_dir = max(dir_paths)
    return pd.read_pickle(os.path.join(latest_dir,'spot.pkl.xz')), \
            pd.read_pickle(os.path.join(latest_dir, 'futures.pkl.xz')), \
            pd.read_pickle(os.path.join(latest_dir, 'pos.pkl.xz'))


def read_spot():
    df_spot = _get_latest()[0]
    return utils.df_table(df_spot)


def read_futures():
    df_futures = _get_latest()[1]
    return utils.df_table(df_futures)


def read_pos():
    df_pos = _get_latest()[2]
    return utils.df_table(df_pos)


def account_agg():
    df_spot, df_futures = _get_latest()[:2]
    df = pd.concat([df_spot[['exchange', 'account', 'value_usd']], df_futures[['exchange', 'account', 'value_usd']]])
    df = df.groupby(['exchange', 'account'], as_index=False).sum()
    df['value_hkd'] = df['value_usd'] * 7.8
    return utils.df_table(df)


def account_total():
    df_spot, df_futures = _get_latest()[:2]
    total_usd = df_spot['value_usd'].sum() + df_futures['value_usd'].sum()
    total_hkd = total_usd * 7.8
    return {
        "columns": [{
            'text': 'value_usd'
        }, {
            'text': 'value_hkd'
        }],
        "rows": [[total_usd, total_hkd]],
        "type": "table"
    }
