"""
项目的根路由表。

用户访问任何地址，Django 都会先来这里匹配 URL。
匹配规则是从上往下，找到第一个能匹配的就执行对应的视图。

本项目有两个入口：
    /admin/  -> Django 自带的后台管理页面
    /api/    -> 我们自己写的接口，交给 core/urls.py 继续细分

举例：
    访问 http://127.0.0.1:8000/api/notes/
    -> 命中 "api/" 前缀
    -> 剩余 "notes/" 交给 core.urls 处理
    -> core.urls 里由 DRF 的 router 匹配到 NoteViewSet
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # 后台管理：用超管账号登录后可以可视化增删改数据
    path("admin/", admin.site.urls),
    # 把我们自己的接口都挂在 /api/ 下，具体规则见 core/urls.py
    path("api/", include("core.urls")),
]
