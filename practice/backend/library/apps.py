"""library 这个 app 的元信息配置。

Django 启动时会扫描每个 app 的 apps.py，读取里面的 AppConfig 类。
虽然不写这个文件程序也能跑（Django 会自动生成默认配置），
但显式写出来更清晰，也方便以后加「启动时执行的逻辑」（ready 方法）。
"""

# AppConfig 是所有 app 配置类的基类。
from django.apps import AppConfig


class LibraryConfig(AppConfig):
    """library app 的配置。

    三个属性的作用：
        default_auto_field
            -> 没有显式声明主键时，用哪种自增字段。
               BigAutoField 是 64 位整数，上限约 922 亿亿，
               比默认的 32 位（约 21 亿）安全得多。
        name
            -> Python 包名，必须是「能 import 的路径」，这里是 library。
               写错会报 ModuleNotFoundError，是新手常见错误。
        verbose_name
            -> admin 后台左侧显示的中文名，会显示成「图书管理」。
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "library"
    verbose_name = "图书管理"
