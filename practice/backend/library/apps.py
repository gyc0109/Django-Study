from django.apps import AppConfig


class LibraryConfig(AppConfig):
    """library 这个 app 的元信息。

    Django 启动时会读取它：
        name           -> Python 包名（library）
        verbose_name   -> 后台显示的中文名
        default_auto_field -> 主键默认用 BigAutoField（64 位自增）
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "library"
    verbose_name = "图书管理"
