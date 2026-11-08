#!/usr/bin/env python
"""
Django 的命令行入口（manage.py）。

===============================================================================
一、为什么每个 Django 项目根目录都有 manage.py？
===============================================================================
它是你和 Django 交互的「总开关」。平时敲的所有命令：

    python manage.py runserver        启动开发服务器
    python manage.py migrate          执行数据库迁移
    python manage.py makemigrations   生成迁移文件
    python manage.py createsuperuser  创建管理员
    python manage.py shell            打开带 Django 环境的 Python 交互
    python manage.py seed_demo        我们自定义的命令（见 library/management/）
    python manage.py test             跑测试

最终都会走到这个文件，再由它把参数交给 Django 的命令行系统。

===============================================================================
二、它做了两件很简单的事
===============================================================================
    1. 告诉 Django「配置文件在哪」（设置 DJANGO_SETTINGS_MODULE）
    2. 把你敲的参数原样转交给 Django 自带的命令解析器
就是这么简单 —— 它本身没有任何业务逻辑。

===============================================================================
三、第一行的 #! 是什么？
===============================================================================
那叫 shebang（也叫 hashbang），Linux/macOS 上用来指定解释器。
有了它并且文件有执行权限（chmod +x manage.py）后，
可以直接 ./manage.py runserver，不必写 python。
Windows 上这一行不起作用，忽略即可。
"""

# os：用来设置环境变量
import os
# sys：拿到命令行参数（sys.argv 就是 ["manage.py", "runserver", ...] 这样的列表）
import sys


def main():
    """命令行主函数。Django 官方模板就是用这个结构，建议不要改。"""
    # 步骤 1：告诉 Django 去哪里找配置。
    # setdefault 的语义：「如果环境变量里还没有这个键，就设置为默认值」。
    # 为什么不直接赋值？因为这样可以在命令行临时覆盖：
    #     DJANGO_SETTINGS_MODULE=config.settings_test python manage.py test
    # 直接赋值的话，你在命令行指定的就会被代码强行覆盖掉。
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    # 步骤 2：导入 Django 的命令行执行器。
    # ★ 为什么 import 放在函数里而不是文件顶部？
    #   因为导入 Django 的模块会触发很多东西（包括读 settings），
    #   放在这里能确保第 1 步的 DJANGO_SETTINGS_MODULE 已经设置好。
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # 常见原因：没激活虚拟环境、没 pip install django。
        # 这里把官方英文提示换成中文，并说明可能原因，方便小白排错。
        # from exc 的作用：保留原始报错链，报错信息里能看到「Caused by」，
        # 不会把真正的原因藏起来。
        raise ImportError(
            "无法导入 Django，请确认虚拟环境已激活、依赖已安装。"
        ) from exc

    # 步骤 3：把命令行参数交给 Django。
    # sys.argv 的例子：["manage.py", "runserver", "0.0.0.0:8001"]
    # execute_from_command_line 会解析它，找到对应命令并执行。
    execute_from_command_line(sys.argv)


# 只有「直接运行这个文件」时才执行 main()。
# 如果被别的文件 import（比如测试代码 import manage），
# __name__ 就不是 "__main__"，main() 不会被执行，避免副作用。
if __name__ == "__main__":
    main()
