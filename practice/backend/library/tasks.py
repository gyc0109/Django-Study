"""Celery 异步任务。

任务必须放在 app 的 tasks.py 里，Celery 才能自动发现。

调用方式对比：
    generate_stock_report(1)        -> 同步执行，当前进程阻塞等待
    generate_stock_report.delay(1)  -> 丢进 Redis 队列，立刻返回 task 对象
"""

import time
from decimal import Decimal

from celery import shared_task
from django.db.models import F, Sum

from .models import Book


@shared_task
def generate_stock_report(delay_seconds=2):
    """生成库存报表（模拟耗时操作）。

    为什么故意 sleep？
        本地数据库数据很少，不 sleep 的话任务瞬间就完成了，
        看不到「排队 -> 执行中 -> 成功」这个过程。

    返回值会被存进 Redis（result backend），前端通过 task_id 轮询取回。
    """
    time.sleep(delay_seconds)

    # count()：图书种类数
    total_titles = Book.objects.count()

    # aggregate(Sum("stock"))：所有书的库存总和
    # 可能没有任何书，此时结果是 None，用 or 0 兜底
    total_stock = Book.objects.aggregate(total=Sum("stock"))["total"] or 0

    # 库存总价值 = sum(stock * price)
    # F() 表示「数据库里的字段值」，让 MySQL 自己算，避免把数据全查到 Python 里
    total_value = (
        Book.objects.aggregate(total=Sum(F("stock") * F("price")))["total"]
        or Decimal("0")
    )

    # Decimal 不能直接 JSON 序列化，转成字符串返回
    return {
        "total_titles": total_titles,
        "total_stock": total_stock,
        "total_value": str(total_value),
    }
