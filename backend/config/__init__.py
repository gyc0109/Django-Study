"""
config 包的初始化文件。

===============================================================================
一、__init__.py 有什么用？
===============================================================================
Python 里，目录下有 __init__.py 才会被当作「包」，才能写
    from config.settings import ...
Django 新建项目时默认生成它，内容一般是空的。

但我们这里要往里面塞两件「必须在项目启动最早期完成」的事：

    1. 把 PyMySQL 伪装成 MySQLdb（否则 Django 连不上 MySQL）
    2. 暴露 celery_app（否则 `celery -A config worker` 找不到应用）

顺序不能反：伪装必须在任何数据库操作之前完成。

===============================================================================
二、为什么要「伪装」？
===============================================================================
Django 的 MySQL 后端源码里写的是：
    import MySQLdb
它只认 mysqlclient 这个库（C 扩展，安装时常常需要编译，Windows 上尤其麻烦）。

PyMySQL 是纯 Python 实现，好装、跨平台，但 Django 不认识这个名字。
于是 PyMySQL 提供了 install_as_MySQLdb()：
执行后它会把自己注册到 sys.modules["MySQLdb"]，
从此 `import MySQLdb` 实际拿到的是 PyMySQL —— 这就是「伪装」，
不改 Django 源码，让 PyMySQL 冒名顶替。

===============================================================================
三、为什么要在这里暴露 celery_app？
===============================================================================
很多 Celery 教程里写的是 `celery -A config worker`。
Celery 会去 config 包里找名为 app 或 celery 的对象。
这里把 celery.py 里的 app 以 celery_app 的名字导出后：
    1. Celery 命令行能找到实例
    2. @shared_task 装饰的任务能绑定到这个 app
       （否则可能出现 "Received unregistered task" 报错）
"""

import pymysql

# 让 Django 的 MySQL 后端使用纯 Python 驱动，免去编译 mysqlclient。
# ★ 这一行必须在任何数据库操作之前执行，所以放在包初始化文件里最保险。
pymysql.install_as_MySQLdb()

# 导入 Celery 实例，并以 celery_app 的名字对外暴露。
#
# noqa: E402 的意思是：这行 import 不在文件最顶部，
# 告诉代码检查工具「我知道，不用警告」。
# 之所以放这里，是因为必须先执行上面的 install_as_MySQLdb()。
from .celery import app as celery_app  # noqa: E402

# __all__ 控制 `from config import *` 时导出哪些名字。
__all__ = ("celery_app",)
