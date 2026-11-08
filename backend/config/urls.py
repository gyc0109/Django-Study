"""
项目的根路由表（config/urls.py）。

===============================================================================
一、URL 是怎么被匹配的？
===============================================================================
用户访问任何地址，Django 都会先来这里匹配。规则是：
    从上往下逐条尝试，找到第一个匹配成功的就执行对应视图。

举例：访问 http://127.0.0.1:8000/api/notes/
    → 命中 "api/" 前缀
    → 剩余 "notes/" 交给 core.urls 继续匹配
    → core.urls 里由 DRF 的 router 匹配到 NoteViewSet
    → NoteViewSet.list() 返回 JSON

===============================================================================
二、本项目只有两个入口
===============================================================================
    /admin/  → Django 自带的后台管理页面
    /api/    → 我们自己写的接口，交给 core/urls.py 继续细分

具体接口全部写在 core/urls.py 里，根路由只做「分发」，
这样每个 app 的路由互不干扰，也方便整个 app 复制到别的项目复用。
"""

# admin：Django 自带的后台站点对象
from django.contrib import admin
# include：把子系统路由挂到某个前缀下
# path：按「路径 + 视图」匹配，支持 <int:id> 这类路径参数
from django.urls import include, path

# urlpatterns 是 Django 约定的变量名，必须叫这个。
urlpatterns = [
    # 后台管理：用超管账号登录后可以可视化增删改数据。
    # 访问 http://127.0.0.1:8000/admin/
    path("admin/", admin.site.urls),

    # 把我们自己的接口都挂在 /api/ 下，具体规则见 core/urls.py。
    # ★ core/urls.py 里写 "notes/"，实际完整地址就是 /api/notes/。
    # ★ 结尾的 "/" 别丢：写成 path("api", ...) 会导致 /api/notes/ 匹配不上。
    path("api/", include("core.urls")),
]
