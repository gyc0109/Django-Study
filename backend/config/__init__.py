"""
包的初始化文件。

Django 在启动时会先导入 config 包（也就是执行这个文件），
我们在这里做两件关键的事情：

1. 把 PyMySQL 伪装成 MySQLdb：
   Django 连接 MySQL 默认需要 mysqlclient（C 扩展，编译麻烦），
   而 PyMySQL 是纯 Python 实现。install_as_MySQLdb() 之后，
   Django 就以为自己在用 MySQLdb，实际走的是 PyMySQL。

2. 暴露 celery_app：
   很多 Celery 教程里写的是 `celery -A config worker`，
   Celery 会去 config 包里找名为 app 或 celery 的对象。
   这里把 celery.py 里的 app 起名叫 celery_app 导出，
   Celery 发现后就能正确加载任务。
"""

import pymysql

# 让 Django 的 MySQL 后端使用纯 Python 驱动，免去编译 mysqlclient
pymysql.install_as_MySQLdb()

# noqa: E402 的意思是：这行 import 不在文件最顶部，
# 告诉代码检查工具「我知道，不用警告」。
from .celery import app as celery_app  # noqa: E402

# __all__ 控制 `from config import *` 时导出哪些名字。
__all__ = ("celery_app",)
