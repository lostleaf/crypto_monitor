import time

def retry_getter(func, retry_seconds, retry_times=3):
    for _ in range(retry_times):
        try:
            return func()
        except Exception as e:
            print(e)
            time.sleep(retry_seconds)
    return None