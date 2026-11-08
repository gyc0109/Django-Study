"""
core/urls.py —— core app 自己的路由表（子路由）

# ==========================================================================
# 一、它和 config/urls.py 是什么关系？
# ==========================================================================
# Django 的路由是「分层的」，像文件夹一样逐级匹配：
#
#   用户访问 /api/notes/?search=django
#        │
#        ▼
#   config/urls.py
#        path("api/", include("core.urls"))
#        │  ← 匹配到 "api/" 前缀，把剩下的 "notes/" 交给 core.urls 继续匹配
#        ▼
#   core/urls.py（本文件）
#        router.register("notes", ...)  ← 匹配 "notes/"，交给 NoteViewSet
#        │
#        ▼
#   NoteViewSet.list()  ← 真正干活的地方
#
# 这样做的好处：每个 app 管自己的路由，互不干扰；
# 以后想把 core 这个 app 挪到别的项目，连路由一起带走就行。
#
# ==========================================================================
# 二、本文件最终暴露的完整接口地址
# ==========================================================================
#   方法     地址                          说明
#   ------   ---------------------------   ----------------------------
#   GET      /api/health/                 健康检查（探 MySQL / Redis）
#   GET      /api/notes/                  笔记列表（分页 + 搜索 + 排序）
#   POST     /api/notes/                  新增笔记
#   GET      /api/notes/{id}/             笔记详情
#   PUT      /api/notes/{id}/             全量更新
#   PATCH    /api/notes/{id}/             局部更新
#   DELETE   /api/notes/{id}/             删除笔记
#   POST     /api/tasks/add/              提交加法异步任务
#   POST     /api/tasks/slow/             提交耗时异步任务
#   GET      /api/tasks/{task_id}/        查询任务状态和结果
#   GET      /api/                        DRF 自动生成的 API 根页面（浏览器可直接点）
#
# ★ 上面 /api/ 前缀不在这里写，是 config/urls.py 的 include 给的。
#   所以本地调试时完整地址是 http://127.0.0.1:8000/api/notes/
# ==========================================================================
"""

# include：把一个子路由表「挂」到当前路由上
# path  ：定义一条静态/半动态路由，从 django.urls 导入
from django.urls import include, path

# DefaultRouter：DRF 提供的路由器，
# 注册 ViewSet 后自动生成一整套 RESTful 路由（含 .json 后缀、API 根视图等）
from rest_framework.routers import DefaultRouter

# 本 app 的 5 个视图
from .views import AddTaskView, HealthView, NoteViewSet, SlowTaskView, TaskStatusView

# ==========================================================================
# 一、先创建路由器
# ==========================================================================
# ★ DefaultRouter vs SimpleRouter：
#   SimpleRouter  只生成增删改查那几条路由；
#   DefaultRouter 额外提供 /api/ 根页面（浏览器打开能看到所有接口列表）
#                 + 自动生成 .json 格式后缀路由，对学习和调试更友好。
#   所以本项目和 practice 都用 DefaultRouter。
router = DefaultRouter()

# ---- 把一个 ViewSet 注册进路由器 ----
router.register(
    "notes",        # ① URL 前缀：最终是 /api/notes/（注意不要写前导斜杠）
    NoteViewSet,    # ② 处理请求的视图类（注意是「类」，不是实例）
    basename="note" # ③ 路由名字前缀，用于反向解析 reverse("note-list") 等
)
# ★ 关于 basename：
#   如果 ViewSet 里有 queryset 属性，DRF 能自动推断出 basename，
#   这时第三个参数可以省略。但显式写出来更清晰，也不容易踩坑
#   （比如 queryset 写成 get_queryset() 方法时，就必须手写 basename）。

# router.register 自动生成的路由如下（prefix 换成你的 "notes"）：
#   GET    /notes/                -> list            note-list
#   POST   /notes/                -> create          note-list
#   GET    /notes/{pk}/           -> retrieve        note-detail
#   PUT    /notes/{pk}/           -> update          note-detail
#   PATCH  /notes/{pk}/           -> partial_update  note-detail
#   DELETE /notes/{pk}/           -> destroy         note-detail
#   GET    /notes/{pk}.{format}/  -> 同上，可加 .json 后缀（DefaultRouter 特有）
#   GET    /                      -> API 根页面（DefaultRouter 特有）


# ==========================================================================
# 二、再声明路由表 urlpatterns
# ==========================================================================
# Django 约定：urls.py 里必须有一个名为 urlpatterns 的列表，
# Django 启动时会读取它。
urlpatterns = [
    # ----------------------------------------------------------------------
    # 1) 健康检查
    # ----------------------------------------------------------------------
    # .as_view()：把「类视图」变成一个 Django 能调用的「函数视图」。
    # ★ 忘记写 .as_view() 是新手最常见的报错之一，会直接 TypeError。
    #
    # name="health"：给这条路由起个名字，
    # 好处是可以用 reverse("health") 拿到 '/api/health/'，
    # 以后改 URL 时不用全局搜索硬编码的路径。
    path("health/", HealthView.as_view(), name="health"),

    # ----------------------------------------------------------------------
    # 2) Celery 任务相关
    # ----------------------------------------------------------------------
    # ★★★ 顺序很重要！★★★
    # Django 的 URL 匹配是「从上往下，匹配到第一条就停」。
    #
    # 如果先写 "tasks/<str:task_id>/"，那么请求 /api/tasks/add/ 时，
    # "add" 会被 <str:task_id> 捕获，交给 TaskStatusView 去查一个叫 add 的任务，
    # 结果永远返回 PENDING —— 这个 bug 非常隐蔽，排查起来很痛苦。
    #
    # 所以规则是：**固定路径必须写在动态路径前面**。 ★★★
    path("tasks/add/", AddTaskView.as_view(), name="task-add"),
    path("tasks/slow/", SlowTaskView.as_view(), name="task-slow"),

    # <str:task_id> 是「路径参数转换器」：
    #   - str  ：匹配除 "/" 之外的任意非空字符串；
    #   - int  ：只匹配正整数，如 <int:pk>；
    #   - slug ：匹配字母/数字/下划线/连字符；
    #   - uuid ：只匹配 UUID 格式。
    #
    # 捕获到的值会以「关键字参数」形式传给视图函数，
    # 所以 TaskStatusView.get(self, request, task_id) 里的参数名
    # 必须和这里写的 task_id 一模一样，否则报 unexpected keyword argument。
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),

    # ----------------------------------------------------------------------
    # 3) 把 router 生成的路由全部挂进来
    # ----------------------------------------------------------------------
    # 前缀写成空字符串 ""，意味着 notes 这些路由直接挂在 /api/ 下
    # （/api/ 前缀由 config/urls.py 提供）。
    #
    # ★ 这一条必须放在最后：router.urls 里包含 /api/ 根页面（空路径），
    #   如果放前面，它会「吃掉」所有请求。
    path("", include(router.urls)),
]
