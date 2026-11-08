"""Celery 应用实例。

Celery 是「异步任务框架」：
    Web 进程只负责把任务丢进队列（Redis），
    另一个后台进程（worker）慢慢执行，用户不用干等。

三个关键点：
1. config_from_object(..., namespace="CELERY")
   读取 settings.py 里所有以 CELERY_ 开头的配置。
2. autodiscover_tasks()
   自动去每个 app 的 tasks.py 里找被 @shared_task 装饰的函数。
3. 启动命令：celery -A config worker -l info
   -A config 表示使用 config 包里的 app 实例。
"""

import os

from celery import Celery

# 让 Celery 也能读到 Django 的配置（尤其是时区）
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("library_practice")

# namespace="CELERY" 意味着配置名要带前缀，例如 CELERY_BROKER_URL
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现所有 app 下的 tasks.py
app.autodiscover_tasks()
