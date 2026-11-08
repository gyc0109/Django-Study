"""
WSGI 入口（Web Server Gateway Interface）。

===============================================================================
一、WSGI 是什么？
===============================================================================
它是 Python 里「Web 服务器」和「Web 应用」之间的通信标准（PEP 3333）。
简单理解成一根插座：
    Web 服务器（gunicorn / uWSGI / mod_wsgi）  ←插头
    WSGI 标准规范                              ←插座
    你的 Django 应用                           ←电器

只要两边都遵守 WSGI，就能随意组合，不用改代码。

===============================================================================
二、这个文件什么时候被用到？
===============================================================================
    【会用到】生产部署：
        gunicorn config.wsgi:application
        意思是「导入 config/wsgi.py 里的 application 变量」
    【不会用到】本地开发：
        python manage.py runserver 走的是 Django 自带的开发服务器，
        它内部会自己调用 get_wsgi_application()，不经过这个文件。

所以这个文件虽然看起来没用，但生产环境部署时必须存在，
Django 新建项目时也会自动生成它。

===============================================================================
三、ASGI 和 WSGI 的区别
===============================================================================
    WSGI  同步：一个请求占一个线程，处理完才能接下一个（简单、稳定）
    ASGI  异步：支持 async/await、WebSocket、长连接（适合实时聊天、推送）

Django 4.x 两种都支持。本项目是普通 REST 接口，WSGI 足够。
"""

# os：设置 DJANGO_SETTINGS_MODULE 环境变量
import os

# Django 提供的工厂函数，负责构建 WSGI 应用对象
from django.core.wsgi import get_wsgi_application

# 告诉 Django：配置在 config/settings.py 里。
# 用 setdefault 而不是直接赋值，是为了允许外部（如部署脚本）覆盖它，
# 从而在同一个代码库里切换不同环境的配置（settings_prod.py 等）。
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# 真正的 WSGI 应用对象。
# 名字必须叫 application —— 这是 WSGI 规范约定的，服务器就找这个名字。
# 它内部会做两件事：加载 settings、初始化所有 app。
application = get_wsgi_application()
