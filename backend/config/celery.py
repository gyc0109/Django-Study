"""
Celery 应用配置。

Celery 是什么？
    一个「异步任务队列」。有些活很慢（发邮件、生成报表、处理图片），
    不能让用户在网页上干等。做法是把任务丢进队列（Redis），
    由后台的 worker 进程慢慢执行，网页立刻返回「任务已提交」。

整体流程：
    前端 POST /api/tasks/add/
        -> Django 视图调用 add.delay(1, 2)
        -> 任务被写进 Redis 队列（broker）
        -> 另一个终端里的 `celery worker` 取出任务并执行
        -> 结果写回 Redis（result backend）
        -> 前端再 GET /api/tasks/{task_id}/ 查询结果

启动 worker 的命令（在 backend 目录）：
    .venv/bin/celery -A config worker -l info
其中 -A config 表示到 config 包里找 Celery 应用。
"""

import os

from celery import Celery

# 让 Celery 知道 Django 的配置文件在哪。
# 这样 worker 执行任务时也能正常使用 Django 的模型、数据库等。
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 创建 Celery 实例，名字叫 django_study（会在日志里显示）。
app = Celery("django_study")

# 从 Django 的 settings.py 里读取所有以 CELERY_ 开头的配置。
# 例如 settings 里的 CELERY_BROKER_URL 会变成 app.conf.broker_url。
# 好处是 Celery 配置和 Django 配置放在同一个文件里，方便管理。
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现任务：
# 去每个已安装 app 的 tasks.py 里找工作，自动注册到 Celery。
# 所以我们的任务写在 core/tasks.py，不需要手动注册。
app.autodiscover_tasks()
