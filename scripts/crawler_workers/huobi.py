import ccxt
import pandas as pd

from utils import retry_getter


def get_account(secret):
    exg = ccxt.huobipro(secret)
    spot_account_id = None
    accounts = retry_getter(exg.private_get_account_accounts, 1)['data']
    for acc in accounts:
        if acc['type'] == 'spot':
            spot_account_id = acc['id']
    spot_data = retry_getter(lambda: exg.private_get_account_accounts_id_balance({'id': spot_account_id}), 1)
    df_spot = pd.DataFrame(spot_data['data']['list'])
    df_spot['balance'] = df_spot['balance'].astype('float')
    df_spot = df_spot[df_spot['balance'] > 0].groupby('currency', as_index=False)[['balance']].sum()
    df_spot['currency'] = df_spot['currency'].str.upper()
    return df_spot, pd.DataFrame(columns=['type', 'currency', 'underlying', 'equity', 'margin_ratio'])
