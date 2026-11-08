import time

from celery import shared_task


@shared_task
def add(a, b):
    """最简单的异步任务，用于验证 Celery worker 是否正常。"""
    return a + b


@shared_task
def slow_task(seconds=3):
    """耗时任务，用于观察任务在后台执行。"""
    time.sleep(seconds)
    return f"已完成 {seconds} 秒的耗时任务"
