import ccxt
import pandas as pd

from utils import retry_getter


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
    return df_spot, \
        pd.DataFrame(columns=['type', 'currency', 'underlying', 'equity', 'margin_ratio']), \
        pd.DataFrame(columns=['instrument_id', 'last', 'qty', 'avg_cost', 'pnl_ratio', 'pnl'])