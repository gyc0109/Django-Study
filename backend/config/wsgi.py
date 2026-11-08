"""
config/wsgi.py —— WSGI 入口（生产部署用）

# ==========================================================================
# 一、WSGI 是什么？
# ==========================================================================
# WSGI（Web Server Gateway Interface）是 Python 界的一套「约定」，
# 规定「Web 服务器（Nginx / uWSGI / Gunicorn）」和
# 「Python 应用（Django）」之间怎么对话。
#
# 打个比方：
#    WSGI 就像「插头和插座的标准」——
#    只要 Django 提供了符合标准的插头（application 变量），
#    任何符合标准的插座（Gunicorn、uWSGI）都能插上。
#
# 请求流向（生产环境）：
#    浏览器 -> Nginx（静态文件 / 反向代理）
#           -> Gunicorn（WSGI 服务器，多进程）
#           -> 本文件暴露的 application
#           -> Django 处理 -> 原路返回
#
# ==========================================================================
# 二、本地开发用得到它吗？
# ==========================================================================
# 基本用不到。
#   python manage.py runserver   -> 用的是 Django 自带的轻量服务器，
#                                   它内部会读取这里的 application，但你不用管。
#   生产环境                     -> gunicorn config.wsgi:application
#                                   注意这里说的是 config.wsgi（模块路径），
#                                   冒号后面是模块里的变量名 application。
#
# ★ 本文件不是给 runserver 用的，但绝不能删：
#   删了之后任何 WSGI 部署方式都会报 "ModuleNotFoundError: config.wsgi"。
# ==========================================================================
"""

# os 用来操作环境变量
import os

# get_wsgi_application() 会返回一个可调用对象（application），
# 它内部完成了 Django 的全部初始化（加载 settings、app registry 等）
from django.core.wsgi import get_wsgi_application

# ---- 告诉 Django「用哪个配置文件」----
# ★ 为什么用 setdefault 而不是直接赋值？
#   setdefault 的语义是「只有当前没设置过，才写入」。
#   这样生产环境可以通过环境变量 DJANGO_SETTINGS_MODULE=config.settings_prod
#   来覆盖，代码一行都不用改。直接写 = 就会把这个能力搞丢。
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# ---- 创建 WSGI 应用对象 ----
# ★ 变量名必须叫 application：
#   Gunicorn / uWSGI 默认就找这个名字（gunicorn config.wsgi 等价于
#   config.wsgi:application）。改成别的名字启动时会报找不到 app。
application = get_wsgi_application()
