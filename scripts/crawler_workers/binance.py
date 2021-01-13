import ccxt
import pandas as pd

from utils import retry_getter


def get_account(secret):
    exg = ccxt.binance(secret)
    df_spot = pd.DataFrame(retry_getter(exg.private_get_account, 1)['balances'])
    df_spot.rename(columns={'asset': 'currency'}, inplace=True)
    df_spot['balance'] = df_spot['free'].astype('float') + df_spot['locked'].astype('float')
    df_spot = df_spot[df_spot['balance'] > 0]
    return df_spot[['currency', 'balance']], \
        pd.DataFrame(columns=['type', 'currency', 'underlying', 'equity', 'margin_ratio']), \
        pd.DataFrame(columns=['instrument_id', 'last', 'qty', 'avg_cost', 'pnl_ratio', 'pnl'])
    