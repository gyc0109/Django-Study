"""WSGI 入口：传统部署方式（gunicorn/uWSGI）会调用这里。

本地开发用 runserver 时基本不会直接用到它，
但保留它是 Django 项目的标准结构。
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()
