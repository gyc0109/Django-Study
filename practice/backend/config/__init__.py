"""
config 包的初始化文件。

===============================================================================
一、__init__.py 有什么用？
===============================================================================
Python 里，一个目录下有 __init__.py 才会被当成「包」（package），
才能用 from config.xxx import yyy 的方式导入。

Django 默认生成这个文件，而且内容通常为空。
但我们这里要往里面塞两件「必须在项目启动最早期执行」的事。

===============================================================================
二、这个文件做两件事，顺序绝对不能乱
===============================================================================
    1. 让 PyMySQL 伪装成 MySQLdb（Django 才能连 MySQL）
    2. 导入 Celery 应用（保证 `celery -A config` 能找到 app）

为什么顺序不能乱？
    伪装必须在 Django 真正去连接数据库之前完成；
    而第 2 步导入 celery 时可能触发 Django 配置加载，
    所以必须放在第 1 步之后。

===============================================================================
三、为什么要「伪装」？（新手最懵的一点）
===============================================================================
Django 的 MySQL 后端代码里写的是：

    import MySQLdb

它默认只认 mysqlclient 这个库（C 语言扩展，Windows 上装它常常要编译、报错）。
PyMySQL 是「纯 Python 实现」的 MySQL 驱动，好装、跨平台。

但 Django 不认识 PyMySQL 这个名字。于是 PyMySQL 提供了
install_as_MySQLdb()：执行后，它会把自己注册到 sys.modules["MySQLdb"]，
于是 `import MySQLdb` 实际拿到的是 PyMySQL —— 这就是「伪装」。

★ 一句话：不改 Django 源码，让 PyMySQL 冒名顶替 mysqlclient。
★ 这个文件必须在「Django 导入数据库后端之前」执行，
  而 Django 启动时第一个加载的就是当前 settings 所在的包（config），
  所以写在这里最保险（manage.py 也能放心 import）。

===============================================================================
四、为什么 __all__ 里要写 celery_app？
===============================================================================
Celery 的官方文档要求：
    在项目包的 __init__.py 里暴露 celery_app

这样有两个作用：
    1. `celery -A config` 能通过 config.celery_app 找到实例
    2. @shared_task 装饰的任务能绑定到这个 app 上（否则可能出现
       "Received unregistered task" 的报错）

__all__ 是「from config import * 时导出哪些名字」的白名单，
写上 celery_app 表示这是本包对外公开的符号。
"""

# 1) 导入 PyMySQL（纯 Python 的 MySQL 驱动）
import pymysql

# 把自己注册成 MySQLdb（上一段解释的「伪装」）。
# ★ 这一行必须在这里执行，且必须在任何数据库操作之前。
pymysql.install_as_MySQLdb()

# 2) 导入 Celery 实例。
#
# 为什么 noqa: E402？
#   PEP8 规定 import 必须写在文件最顶部，
#   但这里我们故意放在 install_as_MySQLdb() 之后（顺序有依赖），
#   所以用 noqa 注释放过 lint 检查，避免被报「import 不在顶部」。
#
# 为什么是 from .celery import app？
#   .celery 是相对导入，等价于 from config.celery import app。
#   把 app 取个别名 celery_app，语义更清楚（一眼看出这是 Celery 的应用实例）。
from .celery import app as celery_app  # noqa: E402

# 对外只暴露 celery_app
__all__ = ("celery_app",)
