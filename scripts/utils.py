import time


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
