"""
config/asgi.py —— ASGI 入口（异步 / WebSocket 用）

# ==========================================================================
# 一、ASGI 是什么？和 WSGI 什么关系？
# ==========================================================================
# WSGI（同步）：一个请求占一个线程/进程，处理完才接下一个。
#              简单稳定，但撑不住「长连接」和「高并发 IO」。
#
# ASGI（异步）：支持 async/await，天生能处理
#              - WebSocket（聊天室、实时推送）
#              - 长轮询、SSE（服务器推送）
#              - 海量并发 IO（比 WSGI 省资源）
#
# 两者的共同点：都是「服务器 ↔ Python 应用」之间的标准接口，
#              都通过一个叫 application 的变量把 Django 暴露出去。
#
# ==========================================================================
# 二、本项目用到 ASGI 吗？
# ==========================================================================
# 用不到。本项目全是普通 HTTP 接口（同步的），
# 生产环境用 gunicorn config.wsgi:application 就够了。
# 这个文件是 django-admin startproject 自动生成的「备用插头」，
# 留着不碍事，等哪天要加 WebSocket（比如 Django Channels）再启用。
#
# ★ 如果真的要用 ASGI：
#     uvicorn config.asgi:application
#   并且加 WebSocket 时，要把这里改成 ProtocolTypeRouter，
#   按协议分流（http 走 Django，websocket 走 Channels）。
# ==========================================================================
"""

# os 用来设置环境变量
import os

# get_asgi_application() 返回一个异步可调用对象
from django.core.asgi import get_asgi_application

# 指定配置文件。★ 用 setdefault 的理由同 wsgi.py：
# 允许生产环境用环境变量覆盖，方便区分 dev / prod 配置。
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# ★ 变量名必须是 application，ASGI 服务器（uvicorn / daphne）默认找这个名字
application = get_asgi_application()
