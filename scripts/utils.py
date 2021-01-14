import time

import pandas as pd


def retry_getter(func, retry_seconds, retry_times=3):
    for _ in range(retry_times):
        try:
            return func()
        except Exception as e:
            print(e)
            time.sleep(retry_seconds)
    return None


def df_table(df):
    return {"columns": [{'text': c} for c in df.columns], "rows": df.values.tolist(), "type": "table"}


def update_dataframe(df_ori, df_new, subset):
    df = pd.concat([df_ori, df_new]).drop_duplicates(subset=subset, keep='last')
    return df.reset_index(drop=True)