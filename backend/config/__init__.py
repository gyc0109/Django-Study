import pymysql

# 让 Django 的 MySQL 后端使用纯 Python 驱动，免去编译 mysqlclient
pymysql.install_as_MySQLdb()

from .celery import app as celery_app  # noqa: E402

__all__ = ("celery_app",)
