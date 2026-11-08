"""
ASGI 入口（Asynchronous Server Gateway Interface）。

===============================================================================
一、ASGI 是什么？
===============================================================================
它是 WSGI 的「异步升级版」，由 Django 官方主导制定。
除了普通的 HTTP 请求，它还支持：
    - WebSocket（实时聊天、实时通知）
    - HTTP/2、长连接（Server-Sent Events）
    - 一个进程并发处理成千上万个连接

===============================================================================
二、什么时候会用到这个文件？
===============================================================================
    【会用到】用 uvicorn / daphne 部署时：
        uvicorn config.asgi:application
    【不会用到】本地 python manage.py runserver：
        它默认走 WSGI；除非你装并指定了 ASGI 服务器。
    【不会用到】本项目现在的所有功能：
        图书 CRUD、缓存、Celery 都是普通 HTTP 请求，WSGI 完全够。

===============================================================================
三、那为什么还要保留它？
===============================================================================
1. Django 新建项目时自动生成，是标准骨架的一部分；
2. 以后要加 WebSocket（比如「报表生成完成」实时推送，而不是轮询），
   直接改配置就能用，不用重新搭结构。
"""

# os：设置 DJANGO_SETTINGS_MODULE 环境变量
import os

# Django 提供的 ASGI 工厂函数
from django.core.asgi import get_asgi_application

# 指定配置文件位置（与 wsgi.py 完全一致）
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# ASGI 应用对象，名字同样必须是 application。
# ★ 注意：如果以后要用 WebSocket，这个文件不能只有这一行，
#   需要把 HTTP 和 WebSocket 两种「路由」组合起来（用 ProtocolTypeRouter），
#   现在保持最简结构即可。
application = get_asgi_application()
