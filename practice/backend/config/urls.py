"""项目总路由。

所有请求先到这里，再按前缀分发：
    /admin/  -> Django 自带后台
    /api/    -> library 这个 app 的接口
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("library.urls")),
]
