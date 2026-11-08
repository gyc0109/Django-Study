"""
Celery 异步任务。

这里的函数不是普通的函数：
    @shared_task 装饰后，它变成了可以"丢进队列后台执行"的任务。

两种调用方式的区别（非常关键）：
    add(1, 2)          -> 立刻在当前进程执行，阻塞等待结果（同步）
    add.delay(1, 2)    -> 只把任务丢进 Redis 队列，立刻返回一个 task 对象，
                          真正的计算由 celery worker 在后台完成（异步）

任务必须写在 tasks.py 里，Celery 才能自动发现（见 config/celery.py）。
"""

import time

from celery import shared_task


@shared_task
def add(a, b):
    """最简单的异步任务，用于验证 Celery worker 是否正常。

    返回 a + b 的结果，结果会被存进 Redis，供前端查询。
    """
    return a + b


@shared_task
def slow_task(seconds=3):
    """耗时任务，用于观察任务在后台执行。

    time.sleep 模拟一个很慢的操作（比如发邮件、处理图片）。
    如果放在普通接口里，用户要干等 3 秒；
    交给 Celery 后，接口立刻返回，用户可以继续操作。
    """
    time.sleep(seconds)
    return f"已完成 {seconds} 秒的耗时任务"
