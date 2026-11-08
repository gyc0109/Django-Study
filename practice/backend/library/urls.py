"""library app 的路由表（最终会被 /api/ 前缀引入）。

完整地址 = /api/ + 下面的路径：
    /api/health/
    /api/categories/
    /api/categories/{id}/
    /api/books/
    /api/books/{id}/
    /api/tasks/report/
    /api/tasks/{task_id}/
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BookViewSet,
    CategoryViewSet,
    HealthView,
    StockReportTaskView,
    TaskStatusView,
)

router = DefaultRouter()
# register 后自动生成列表和详情两组路由，不用手写 6 条 path
router.register("categories", CategoryViewSet, basename="category")
router.register("books", BookViewSet, basename="book")

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),

    # 具体路径要写在变量路径前面，
    # 否则 "report" 会被 <str:task_id> 当成任务 id 匹配走
    path("tasks/report/", StockReportTaskView.as_view(), name="task-report"),
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),

    # 把 router 自动生成的路由全部挂进来
    path("", include(router.urls)),
]
