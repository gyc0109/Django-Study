"""
Celery 应用配置（config/celery.py）。

===============================================================================
一、Celery 是什么？
===============================================================================
一个「异步任务队列」。有些活很慢（发邮件、生成报表、处理图片），
不能让用户在网页上干等。做法是：
    把任务丢进队列（Redis）→ 后台 worker 慢慢执行 → 网页立刻返回「已提交」

整体流程（本项目）：
    前端 POST /api/tasks/add/ {"a":7,"b":35}
        ↓
    Django 视图调用 add.delay(7, 35)          ← 只是「投递」，毫秒级返回
        ↓
    任务被写进 Redis 队列（broker，0 号库）
        ↓
    另一个终端里的 `celery worker` 取出任务并执行
        ↓
    结果写回 Redis（result backend，也是 0 号库）
        ↓
    前端 GET /api/tasks/{task_id}/ 查询结果

★ 三个进程必须都在跑：
    python manage.py runserver（生产者）
    celery -A config worker -l info（消费者）
    Redis 容器（队列 + 结果仓库）
  少了 worker，任务会永远停留在 PENDING。

===============================================================================
二、启动 worker 的命令（在 backend 目录下）
===============================================================================
    .venv/bin/celery -A config worker -l info

  -A config   表示「到 config 这个包里找 Celery 应用实例」
              能找到是因为 config/__init__.py 里导出了 celery_app
  worker      子命令：启动消费者进程
  -l info     日志级别：info（能看到每个任务被接收、完成）
"""

# os：用来设置环境变量，让 Celery 进程也能读到 Django 的配置
import os

# Celery 主类
from celery import Celery

# 让 Celery 知道 Django 的配置文件在哪。
# 这样 worker 执行任务时也能正常使用 Django 的模型、数据库、缓存等。
# 用 setdefault 是为了允许命令行/外部环境覆盖
# （如 DJANGO_SETTINGS_MODULE=config.settings_test）。
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 创建 Celery 实例，名字叫 django_study。
# 这个名字会出现在 worker 的启动日志里，方便区分多个项目。
# ★ 起什么名字都行，不要求和 Django 项目名一致。
app = Celery("django_study")

# 从 Django 的 settings.py 里读取所有以 CELERY_ 开头的配置。
#   "django.conf:settings" 是「模块:变量名」写法，等价于
#       from django.conf import settings
#   namespace="CELERY" 会自动去掉前缀：
#       settings.CELERY_BROKER_URL   → app.conf.broker_url
#       settings.CELERY_TIMEZONE     → app.conf.timezone
# 好处：Celery 配置和 Django 配置放在同一个文件里，只维护一处。
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现任务：
# 去每个已安装 app 的 tasks.py 里找被 @shared_task 装饰的函数，自动注册。
# 所以我们的任务写在 core/tasks.py，不需要手动 import 或注册。
# ★ 文件名必须正好叫 tasks.py（或在 app 里显式声明），否则找不到。
app.autodiscover_tasks()
