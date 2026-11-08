"""
core/apps.py —— app 的「身份证」与启动配置

Django 启动时，会为 INSTALLED_APPS 里的每个 app 找一个 AppConfig 子类，
用它来登记这个 app 的基本信息（叫什么、显示什么名、启动时做什么）。

绝大多数情况下这个文件是 django-admin startapp 自动生成的，不需要改。
只有两种场景会动它：
    1. 想在后台把 app 名字改成中文 -> 加 verbose_name；
    2. app 启动时要自动做点事（比如注册信号）-> 复写 ready()。
"""

# AppConfig 是所有 app 配置类的基类
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """core 这个 app 的配置类。

    ★ 命名规则：Django 会按「<AppName>Config」去找，
      而且 settings.INSTALLED_APPS 里写 "core" 时，
      它会去 core/apps.py 里自动找 CoreConfig 并用它。
    """

    # ---- 主键字段的默认类型 ----
    # BigAutoField = 64 位自增整数（对应 MySQL 的 bigint）。
    # ★ 为什么必须是它？
    #   Django 3.2 之前默认用 AutoField（32 位 int），最大约 21 亿，
    #   高并发写入的表（日志、订单）几年后可能真的爆掉。
    #   所以新项目统一用 BigAutoField，避免以后改主键类型（那是个大工程）。
    #   如果你在 settings 里设了 DEFAULT_AUTO_FIELD，这里的值会被它覆盖，
    #   但显式写出来更清晰。
    default_auto_field = "django.db.models.BigAutoField"

    # ---- app 的 Python 路径 ----
    # "core" 表示这个 app 是项目根目录下的 core 包。
    # ★ 这个值必须和 settings.INSTALLED_APPS 里的字符串完全一致，
    #   否则 Django 会报 "Cannot import 'core'"。
    name = "core"

    # ---- 后台显示名（本项目用默认值，所以注释掉了）----
    # verbose_name = "笔记管理"
    #
    # ---- 启动钩子（同样用不到，注释掉）----
    # def ready(self):
    #     """所有 app 加载完后调用，常用来注册 signal 或做启动检查。"""
    #     from . import signals  # noqa: F401
