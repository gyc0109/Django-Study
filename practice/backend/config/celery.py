"""
Celery 应用实例（整个项目只有这一个）。

===============================================================================
一、Celery 是干什么的？
===============================================================================
它是「异步任务框架」，解决「某个操作太慢，不能让用户干等」的问题。

本项目的例子：
    点击「生成库存报表」→ 要统计所有书的库存 × 价格
    如果只用几千条数据，其实一瞬间就完了；
    但假设有 100 万条，可能要 10 秒 —— 用户点一下转 10 秒圈圈很难受。

Celery 的做法：
    Web 进程只负责把任务「丢进队列」（毫秒级返回 202 Accepted）
    另一个独立的后台进程（worker）慢慢执行
    前端拿一个 task_id 去轮询进度和结果

===============================================================================
二、三个进程的分工（很重要，不然会搞混）
===============================================================================
    Django (runserver)  生产者：task.delay() 把任务丢进 Redis
    Redis               中转站：队列 + 结果仓库
    Celery worker       消费者：真正执行 update_stock_report()

    如果 worker 没启动，任务会一直处于 PENDING（排队中），
    前端就会一直转圈 —— 这是新手最常踩的坑。

===============================================================================
三、三个关键点
===============================================================================
1. config_from_object(..., namespace="CELERY")
   把 settings.py 里所有以 CELERY_ 开头的配置读进来。
   namespace 的作用是「自动加前缀」：
       settings 里的 CELERY_BROKER_URL → Celery 里的 broker_url
       settings 里的 CELERY_TIMEZONE   → Celery 里的 timezone

2. autodiscover_tasks()
   自动去 INSTALLED_APPS 里每个 app 的 tasks.py 中找被 @shared_task 装饰的函数。
   所以只要文件叫 tasks.py 且放在 app 目录下，就会被自动注册，不用手动 import。

3. 启动命令（在 backend 目录、虚拟环境激活的状态下）：
       celery -A config worker -l info
   -A config 的意思是「用 config 这个包里名为 app 的 Celery 实例」。
   为什么能找到？因为 config/__init__.py 里写了
       from .celery import app as celery_app
"""

# os：用于设置环境变量，让 Celery 进程也能读到 Django 的配置
import os

# Celery 的主类。from celery import Celery 是官方推荐的写法。
from celery import Celery

# 让 Celery 也读到 Django 的配置（尤其是 DATABASES、时区等）。
# setdefault 的意思是「如果外部已经设置过，就不覆盖」，
# 这样你在命令行用 DJANGO_SETTINGS_MODULE=xxx.settings 也能临时指定别的配置。
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 创建 Celery 实例。
# 第一个参数 "library_practice" 是应用名，会出现在 worker 的启动日志里
# （如 [tasks] . library.tasks.update_stock_report），方便区分多个项目。
# ★ 这个字符串可以随便写，只要不和别的 Celery 项目重名就行。
app = Celery("library_practice")

# 从 Django 的 settings 模块读取配置。
# "django.conf:settings" 是「模块路径:变量名」的写法，等价于
#     from django.conf import settings
# namespace="CELERY" 是约定俗成的：所有 Celery 相关配置都以 CELERY_ 开头，
# 这样能和 Django 自己的配置混在同一个文件里而不冲突。
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现任务：
# 去每个已安装 app 的 tasks.py 里找 @shared_task 函数。
# 假如以后新增了 app（如 report），只要它下面有 tasks.py，这里不用改就能被识别。
app.autodiscover_tasks()
