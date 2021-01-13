import ccxt
import pandas as pd
from utils import retry_getter


def extract_okex_funding_spot(df):
    if df.empty:
        return pd.DataFrame(columns=['currency', 'balance'])
    df['balance'] = pd.to_numeric(df['balance'])
    df = df[df['balance'] > 0]
    return df[['currency', 'balance']]


def extract_okex_futures_swap(df):
    if df.empty:
        return pd.DataFrame(columns=['currency', 'underlying', 'equity', 'margin_ratio'])
    df['equity'] = df['equity'].astype('float')
    df['margin_ratio'] = df['margin_ratio'].astype('float')
    return df[['currency', 'underlying', 'equity', 'margin_ratio']]


def get_account(secret):
    exg = ccxt.okex(secret)

    # Funding and spot
    df_funding = pd.DataFrame(retry_getter(exg.account_get_wallet, 1))
    df_funding = extract_okex_funding_spot(df_funding)
    df_spot = pd.DataFrame(retry_getter(exg.spot_get_accounts, 1))
    df_spot = extract_okex_funding_spot(df_spot)
    df_spot = pd.concat([df_funding, df_spot]).groupby('currency', as_index=False).sum()

    # Futures and swap
    df_futures = pd.DataFrame(retry_getter(exg.futures_get_accounts, 10)['info']).T
    df_futures = extract_okex_futures_swap(df_futures)
    df_futures['type'] = 'futures'
    df_swap = pd.DataFrame(retry_getter(exg.swap_get_accounts, 10)['info'])
    df_swap = extract_okex_futures_swap(df_swap)
    df_swap['type'] = 'swap'
    df_futures = pd.concat([df_futures, df_swap])

    position_info = exg.futures_get_position()['holding']
    df_pos = pd.DataFrame(sum(position_info, []), dtype=float)

    if not df_pos.empty:
        df_long = df_pos[['instrument_id', 'last', 'long_qty', 'long_avg_cost', 'long_pnl_ratio', 'long_pnl']]
        df_long = df_long.rename(columns={
            'long_qty': 'qty',
            'long_avg_cost': 'avg_cost',
            'long_pnl_ratio': 'pnl_ratio',
            'long_pnl': 'pnl'
        })
        df_short = df_pos[['instrument_id', 'last', 'short_qty', 'short_avg_cost', 'short_pnl_ratio', 'short_pnl']]
        df_short = df_short.rename(columns={
            'short_qty': 'qty',
            'short_avg_cost': 'avg_cost',
            'short_pnl_ratio': 'pnl_ratio',
            'short_pnl': 'pnl'
        })
        df_short['qty'] = -df_short['qty']
        df_pos = pd.concat([df_long, df_short])
        df_pos = df_pos[df_pos['qty'] != 0]
    else:
        df_pos = pd.DataFrame(columns=['instrument_id', 'last', 'qty', 'avg_cost', 'pnl_ratio', 'pnl'])

    return df_spot, df_futures, df_pos
