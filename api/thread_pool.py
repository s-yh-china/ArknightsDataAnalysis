import time
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()


class MyThreadPool:
    @staticmethod
    def run_async(method, *args):
        executor.submit(method, *args)
    
    @staticmethod
    def register_async_timer(method, pre_time, *args):
        executor.submit(sync_timer, method, pre_time, *args)


def sync_timer(method, pre_time, *args):
    while True:
        executor.submit(method, *args)
        time.sleep(pre_time)
        