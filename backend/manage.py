#!/usr/bin/env python
"""
Django 命令行工具入口（manage.py）。

===============================================================================
一、它是干什么的？
===============================================================================
平时执行的这些命令，本质上都是在运行这个文件：
    python manage.py runserver        启动开发服务器
    python manage.py migrate          把模型变更同步到数据库
    python manage.py makemigrations   生成迁移文件
    python manage.py createsuperuser  创建超级管理员
    python manage.py shell            打开带 Django 环境的交互式 Python
    python manage.py test             运行测试

===============================================================================
二、它只做两件事
===============================================================================
    1. 告诉 Django「配置文件在哪」
    2. 把命令行参数交给 Django 自己处理
本身没有任何业务逻辑。

===============================================================================
三、第一行 #! 是什么？
===============================================================================
shebang，用来指定解释器（Linux/macOS 有效）。
加了执行权限（chmod +x manage.py）后可以直接 ./manage.py runserver。
Windows 上这行不起作用，忽略即可。
"""

# os：设置环境变量
import os
# sys：拿到命令行参数（sys.argv = ["manage.py", "runserver", ...]）
import sys


def main():
    """命令行主函数。Django 官方模板就是这种结构，建议不要改。"""
    # 指定配置文件为 config/settings.py。
    # 设置成环境变量后，Django 的各个模块都能读到。
    # 用 setdefault 而不是直接赋值：允许命令行临时覆盖，例如
    #   DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        # 这里才真正导入 Django。
        # ★ 放在函数内而不是文件顶部：导入 Django 会触发读 settings，
        #   必须等上一行的环境变量设置好之后再导入。
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # 常见原因：没激活虚拟环境、没 pip install django。
        # from exc 保留原始报错链，方便定位真正原因。
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # 把命令行参数（sys.argv）交给 Django 解析并执行对应命令。
    # 例如 ["manage.py", "runserver", "0.0.0.0:8000"]。
    execute_from_command_line(sys.argv)


# 只有直接运行这个文件时才执行 main()；
# 被别的模块 import 时（__name__ 不是 "__main__"）不会执行，避免副作用。
if __name__ == "__main__":
    main()
