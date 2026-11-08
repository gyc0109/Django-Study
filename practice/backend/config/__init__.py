"""config 包的初始化文件。

这里做两件事，顺序都不能乱：
1. 让 PyMySQL 伪装成 MySQLdb，Django 才能用纯 Python 驱动连 MySQL；
2. 导入 Celery 应用，保证 Django 启动时 Celery 也一起初始化。

为什么要伪装？
    Django 默认只认 mysqlclient（C 扩展，安装时可能要编译）。
    PyMySQL 是纯 Python 实现，执行 install_as_MySQLdb() 后，
    Django 会以为它就是 mysqlclient，从而正常连接。
"""

import pymysql

pymysql.install_as_MySQLdb()

from .celery import app as celery_app  # noqa: E402

__all__ = ("celery_app",)
