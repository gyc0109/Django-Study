"""
项目总路由（根 URLconf）。

===============================================================================
一、URL 是怎么被找到的？
===============================================================================
Django 处理一个请求的流程：

    http://127.0.0.1:8001/api/books/?page=2
    ↓
    settings.py 里 ROOT_URLCONF = "config.urls"   ← 先找到这个文件
    ↓
    按 urlpatterns 从上往下一项项匹配
    ↓
    path("api/", include("library.urls")) 匹配到 "api/" 前缀
    ↓
    剩下的 "books/?page=2" 交给 library/urls.py 继续匹配
    ↓
    最终落到某个视图函数/类

★ 匹配规则是「从上到下，第一个匹配成功的就用」，
  所以顺序很重要（越具体的路径越要写在前面）。

===============================================================================
二、这个文件只做分发，不写具体业务
===============================================================================
真实项目里，根路由通常只写：
    - admin 后台
    - 各个 app 的 include
    - 可能的健康检查、调试工具路由

具体接口全部写在各自的 app/urls.py 里，这样职责清晰，
也能把 app 整个复制到另一个项目复用。

===============================================================================
三、本项目的路由总览
===============================================================================
    /admin/                  Django 自带后台（可视化增删改查数据库）
    /api/categories/         分类（只读 List + 详情）
    /api/books/              图书（完整 CRUD + 分页 + 搜索 + 排序）
    /api/tasks/report/       触发「生成库存报表」异步任务
    /api/tasks/<task_id>/    查询某个异步任务的状态/结果
"""

# admin：Django 自带的后台管理站点对象
from django.contrib import admin
# include：把「子系统路由」挂到某个前缀下，是最常用的路由函数
# path：按「路径 + 视图」精确匹配，支持 <int:id> 这样的路径参数
from django.urls import include, path

# urlpatterns 是 Django 约定的变量名，必须叫这个，Django 只认它。
urlpatterns = [
    # Django 自带的后台管理。
    # 访问 http://127.0.0.1:8001/admin/ ，用超级用户登录，
    # 可以图形化地管理 books / categories（配置见 library/admin.py）。
    path("admin/", admin.site.urls),

    # 把 library 这个 app 的所有路由挂到 /api/ 下。
    # include 的好处：library/urls.py 里写 "books/"，实际访问路径是 "/api/books/"。
    # ★ 结尾的 "/" 别丢：如果写成 path("api", ...)，那么 /api/books/ 就匹配不上了。
    path("api/", include("library.urls")),
]
