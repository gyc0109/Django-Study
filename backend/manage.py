"""
Django 命令行工具入口。

平时执行的这些命令，本质上都是在运行这个文件：
    python manage.py runserver     # 启动开发服务器
    python manage.py migrate       # 把模型变更同步到数据库
    python manage.py createsuperuser

它做的事情很简单：
1. 告诉 Django「配置文件在哪」
2. 把你在命令行输入的参数交给 Django 自己处理
"""

import os
import sys


def main():
    # 指定配置文件为 config/settings.py。
    # 设置成环境变量后，Django 的各个模块都能读到。
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        # 这里才真正导入 Django。如果没装 Django，会进入 except 给出提示。
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # 把命令行参数（sys.argv）交给 Django 解析并执行对应命令。
    execute_from_command_line(sys.argv)


# 只有直接运行这个文件时才执行 main()，被 import 时不会执行。
if __name__ == "__main__":
    main()
