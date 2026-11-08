"""Celery 异步任务。

任务函数必须放在「已安装 app」的 tasks.py 里，Celery 才能自动发现
（见 config/celery.py 的 autodiscover_tasks()）。

两种调用方式的区别（非常关键）：
    generate_stock_report(1)        -> 同步执行：当前进程阻塞，等结果算完才返回
    generate_stock_report.delay(1)  -> 异步执行：只把任务丢进 Redis 队列，
                                       立刻返回一个 task 对象，计算由 worker 后台完成

Web 请求里一定要用 .delay()，否则「异步」就白做了。
"""

# time 用来模拟耗时操作（time.sleep）。
import time

# Decimal 表示十进制小数；数据库里 price 是 DECIMAL 类型，
# 聚合结果也是 Decimal，不能直接 JSON 序列化，后面要转成字符串。
from decimal import Decimal

# shared_task 是 Celery 提供的装饰器：
# 不用绑定具体的 app 实例，就能把普通函数注册成任务。
from celery import shared_task

# F 表示「数据库字段的引用」；Sum 是聚合函数（对应 SQL 的 SUM）。
from django.db.models import F, Sum

# 干活要用到模型，所以导入 Book。
from .models import Book


@shared_task
def generate_stock_report(delay_seconds=2):
    """生成一份库存报表，返回汇总数据。

    为什么故意 sleep 2 秒？
        本地数据库只有十几条数据，不 sleep 的话任务在一瞬间就完成，
        前端看不到「PENDING -> STARTED -> SUCCESS」的状态变化。
        sleep 是为了让异步过程「看得见」，真实项目里换成真正的耗时操作
        （导出 Excel、调第三方接口、处理图片等）。

    参数：
        delay_seconds：模拟耗时多少秒，默认 2；可以通过 .delay(5) 覆盖。

    返回值：
        必须是「能被 JSON 序列化」的类型（dict / list / str / int ...），
        因为 Celery 会把它写进 Redis 的 result backend。
        这里返回 dict，其中 Decimal 已转成字符串。
    """
    # 模拟耗时：这 2 秒里 worker 在忙，但 Web 进程早就把 202 返回给前端了。
    time.sleep(delay_seconds)

    # ------------------------------------------------------------
    # 1) 图书种类数：SELECT COUNT(*) FROM library_book
    # ------------------------------------------------------------
    total_titles = Book.objects.count()

    # ------------------------------------------------------------
    # 2) 所有书的库存总和：SELECT SUM(stock) FROM library_book
    # aggregate() 返回一个字典，键是我们起的别名 total。
    # 表里一本书都没有时，SUM 的结果是 NULL -> Python 的 None，
    # 所以用 `or 0` 兜底，保证返回的是数字而不是 null。
    # ------------------------------------------------------------
    total_stock = Book.objects.aggregate(total=Sum("stock"))["total"] or 0

    # ------------------------------------------------------------
    # 3) 库存总价值 = sum(stock * price)
    # F("stock") 表示「数据库里 stock 这一列的值」，
    # 所以 SUM(stock * price) 这句计算完全交给 MySQL 做，
    # 不用先把所有书查进 Python 再循环相乘（数据量大时差距非常明显）。
    # 同样，没有数据时 SUM 返回 NULL，用 Decimal("0") 兜底。
    # ------------------------------------------------------------
    total_value = (
        Book.objects.aggregate(total=Sum(F("stock") * F("price")))["total"]
        or Decimal("0")
    )

    # ------------------------------------------------------------
    # 返回结果。
    # Decimal 不能直接 JSON 序列化（会报 TypeError），
    # 所以用 str() 转成 "7475.20" 这样的字符串。
    # 前端如果需要计算，再 Number(...) 转回去即可。
    # ------------------------------------------------------------
    return {
        "total_titles": total_titles,
        "total_stock": total_stock,
        "total_value": str(total_value),
    }
