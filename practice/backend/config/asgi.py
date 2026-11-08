"""ASGI 入口：支持异步/WebSocket 的部署方式会调用这里。

本项目暂时用不到，但保留标准结构，以后要上异步服务时不用重建。
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
