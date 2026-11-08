#!/usr/bin/env python
"""Django 的命令行入口。

平时执行的所有 manage.py 命令（runserver、migrate、shell...），
最终都是从这里开始的：
    1. 把 DJANGO_SETTINGS_MODULE 指向 config/settings.py
    2. 交给 Django 自带的命令行工具去解析参数
"""

import os
import sys


def main():
    # 告诉 Django：配置在 config/settings.py 里
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入 Django，请确认虚拟环境已激活、依赖已安装。"
        ) from exc
    # 把你在终端敲的参数原样交给 Django
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
