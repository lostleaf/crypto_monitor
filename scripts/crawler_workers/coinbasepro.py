import ccxt
import pandas as pd

from utils import retry_getter


def get_account(secret):
    exg = ccxt.coinbasepro(secret)
    df_spot = pd.DataFrame(retry_getter(exg.private_get_accounts, 1))
    df_spot['balance'] = df_spot['balance'].astype('float')
    return df_spot[['currency', 'balance']], \
        pd.DataFrame(columns=['type', 'currency', 'underlying', 'equity', 'margin_ratio'])