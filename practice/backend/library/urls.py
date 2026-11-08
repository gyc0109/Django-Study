"""library app 的路由表。

它会被 config/urls.py 以 `path("api/", include("library.urls"))` 引入，
所以「完整地址 = /api/ + 下面写的路径」。

最终对外提供的地址：
    /api/health/             健康检查
    /api/categories/         分类列表（GET）/ 新增（POST）
    /api/categories/{id}/    分类详情（GET）/ 更新（PUT/PATCH）/ 删除（DELETE）
    /api/books/              图书列表（GET）/ 新增（POST）
    /api/books/{id}/         图书详情（GET）/ 更新（PUT/PATCH）/ 删除（DELETE）
    /api/tasks/report/       提交「生成库存报表」异步任务（POST）
    /api/tasks/{task_id}/    查询任务状态和结果（GET）
    /api/                    DRF 自动生成的 API 根页面（列出上面这些入口）

Django 的 URL 匹配规则：
    从上往下逐条尝试，命中第一条就停止。
    所以「固定路径」必须写在「带变量的路径」前面。
"""

# path() 定义一条路由；include() 把另一个路由表整体挂到某个前缀下。
from django.urls import include, path

# DefaultRouter 是 DRF 的路由器：注册 ViewSet 后自动生成一整套 RESTful 路由。
from rest_framework.routers import DefaultRouter

# 导入本 app 的视图类。
from .views import (
    BookViewSet,
    CategoryViewSet,
    HealthView,
    StockReportTaskView,
    TaskStatusView,
)

# ------------------------------------------------------------
# 1) 先创建路由器
# ------------------------------------------------------------
router = DefaultRouter()

# register(前缀, 视图类, basename=路由名前缀)
# 注册之后，DRF 会自动生成这些路由（不用手写 6 条 path）：
#   GET    /categories/        列表
#   POST   /categories/        新增
#   GET    /categories/{pk}/   详情
#   PUT    /categories/{pk}/   全量更新
#   PATCH  /categories/{pk}/   局部更新
#   DELETE /categories/{pk}/   删除
# basename 用于反向解析（例如 reverse("category-list")），一般用模型名。
router.register("categories", CategoryViewSet, basename="category")
router.register("books", BookViewSet, basename="book")

# ------------------------------------------------------------
# 2) 再写 urlpatterns 列表
# ------------------------------------------------------------
urlpatterns = [
    # .as_view() 把「类视图」变成一个 Django 能调用的函数。
    # 不写 name 也能跑，但写了以后可以用 reverse("health") 生成地址，
    # 前端/测试里就不需要硬编码 "/api/health/" 字符串。
    path("health/", HealthView.as_view(), name="health"),

    # ---------------- 异步任务相关 ----------------
    # 顺序非常重要：具体的 "tasks/report/" 必须写在
    # 带变量的 "tasks/<str:task_id>/" 前面。
    # 否则请求 /api/tasks/report/ 会先命中 <str:task_id>，
    # 把 "report" 当成任务 id 传进 TaskStatusView，导致查不到任务。
    path("tasks/report/", StockReportTaskView.as_view(), name="task-report"),

    # <str:task_id> 是「路径参数」：
    #   把 URL 里这一段捕获成字符串，作为关键字参数传给视图函数。
    #   例如 /api/tasks/abc-123/ -> view(request, task_id="abc-123")
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),

    # ---------------- 自动生成的路由 ----------------
    # "" 表示「不额外加前缀」，直接使用 router 生成的那些路径。
    # include() 会把 router.urls 里的每一条路由展开合并进来。
    path("", include(router.urls)),
]
