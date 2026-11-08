"""
core app 的路由表（会被 config/urls.py 以 /api/ 前缀引入）。

最终完整的接口地址 = /api/ + 这里的路径：
    /api/health/            健康检查
    /api/notes/             笔记列表（GET）与新增（POST）
    /api/notes/{id}/        详情（GET）、更新（PUT/PATCH）、删除（DELETE）
    /api/tasks/add/         提交加法异步任务
    /api/tasks/slow/        提交耗时异步任务
    /api/tasks/{task_id}/   查询任务状态和结果

注意 router.urls 还会自动生成一个 API 根页面 /api/。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AddTaskView, HealthView, NoteViewSet, SlowTaskView, TaskStatusView

# DefaultRouter 是 DRF 的路由器：
# 只要把一个 ViewSet 注册进去，它就自动生成一整套 RESTful 路由，
# 不用手写每一条 path。
router = DefaultRouter()
# 参数含义：
#   "notes"       -> URL 前缀，最终是 /api/notes/
#   NoteViewSet   -> 处理请求的视图类
#   basename      -> 路由名字前缀，用于反向解析（一般用模型名）
router.register("notes", NoteViewSet, basename="note")

urlpatterns = [
    # .as_view() 把「类」变成 Django 能调用的「函数视图」
    path("health/", HealthView.as_view(), name="health"),

    # 异步任务相关：先声明具体的 add/slow，再声明带变量的 task_id，
    # 顺序不能反，否则 "add" 会被当成 task_id 匹配走。
    path("tasks/add/", AddTaskView.as_view(), name="task-add"),
    path("tasks/slow/", SlowTaskView.as_view(), name="task-slow"),
    # <str:task_id> 会把 URL 里的这一段捕获成参数传给视图
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),

    # 把路由器自动生成的 notes 相关路由全部挂进来
    path("", include(router.urls)),
]
