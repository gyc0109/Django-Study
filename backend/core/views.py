"""
视图（View）—— 接口的具体逻辑都写在这里。

Django 的请求流程：
    URL 匹配到某个视图  ->  视图函数/类接收 request  ->  处理
    ->  返回 Response（DRF 会把它转成 JSON）

本项目有两类视图：
1. APIView：最基础，像写普通函数一样，自己处理 GET/POST。
2. ModelViewSet：DRF 提供的"全家桶"，一个类自动拥有
   列表、新增、详情、更新、删除 6 个接口，配合 router 使用。
"""

from celery.result import AsyncResult
from django.core.cache import cache
from django.db import connection
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Note
from .serializers import NoteSerializer
from .tasks import add, slow_task


class HealthView(APIView):
    """健康检查接口：GET /api/health/

    用来确认 Django 自身、MySQL、Redis 是否都能连上。
    前端点「刷新」时调用的就是它。
    """

    def get(self, request):
        # ---- 检查 MySQL ----
        # connection 是当前数据库连接；ensure_connection() 会尝试真正连一次。
        # 连不上会抛异常，所以用 try/except 包起来，避免整个接口 500。
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False

        # ---- 检查 Redis ----
        # 往缓存写一个值再读出来，能读到说明 Redis 正常。
        # timeout=10 表示 10 秒后自动过期，不留垃圾数据。
        try:
            cache.set("health", "ok", timeout=10)
            redis_ok = cache.get("health") == "ok"
        except Exception:
            redis_ok = False

        # 两个都正常才算 ok，否则是 degraded（降级）
        status_text = "ok" if db_ok and redis_ok else "degraded"
        return Response(
            {"status": status_text, "db": db_ok, "redis": redis_ok},
            # 正常返回 200，异常返回 503（服务不可用），方便监控工具判断
            status=status.HTTP_200_OK if status_text == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class NoteViewSet(viewsets.ModelViewSet):
    """MySQL CRUD + 搜索 + 分页示例。

    ModelViewSet 自动提供以下接口（配合 core/urls.py 的 router）：
    - GET    /api/notes/?search=关键词&page=1   列表（分页 + 搜索）
    - POST   /api/notes/                       新增
    - GET    /api/notes/{id}/                  详情
    - PUT    /api/notes/{id}/                  全量更新（所有字段都要传）
    - PATCH  /api/notes/{id}/                  局部更新（只传要改的字段）
    - DELETE /api/notes/{id}/                  删除

    我们只需要声明 4 个属性，增删改查的逻辑 DRF 已经写好。
    """

    # 查哪些数据：Note.objects.all() 等价于 SELECT * FROM core_note
    queryset = Note.objects.all()
    # 用哪个序列化器把对象转成 JSON / 把 JSON 转成对象
    serializer_class = NoteSerializer

    # ?search=xxx 会在这些字段里做 icontains 模糊匹配（不区分大小写）
    search_fields = ["title", "content"]

    # 支持 ?ordering=created_at、?ordering=-created_at 等
    ordering_fields = ["id", "created_at", "title"]
    # 默认排序（前端不传 ordering 时生效）
    ordering = ["-id"]

    # 分页已在 settings.REST_FRAMEWORK 里全局配置（每页 5 条），
    # 如果想只给这个接口单独设置，可以取消下面两行注释：
    # pagination_class = PageNumberPagination
    # pagination_class.page_size = 5


class AddTaskView(APIView):
    """提交一个 Celery 加法任务：POST /api/tasks/add/

    请求体：{"a": 7, "b": 35}
    响应：{"task_id": "xxxx"}，之后用这个 id 去查结果。
    """

    def post(self, request):
        # request.data 是 DRF 解析好的请求体（JSON 会自动变成字典）
        try:
            a = int(request.data.get("a", 0))
            b = int(request.data.get("b", 0))
        except (TypeError, ValueError):
            # 参数不是整数时返回 400，告诉前端请求有问题
            return Response({"detail": "a 和 b 必须是整数"}, status=status.HTTP_400_BAD_REQUEST)

        # .delay() 是关键：把任务丢进 Redis 队列，立即返回，不阻塞请求
        task = add.delay(a, b)
        # 202 Accepted：表示"已接收，稍后处理"，比 200 更准确
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class SlowTaskView(APIView):
    """提交一个 Celery 耗时任务：POST /api/tasks/slow/

    请求体：{"seconds": 5}
    用来体验"接口秒回，任务后台跑"的效果。
    """

    def post(self, request):
        # 没传 seconds 时默认 3 秒
        seconds = int(request.data.get("seconds", 3))
        task = slow_task.delay(seconds)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class TaskStatusView(APIView):
    """查询 Celery 任务状态与结果：GET /api/tasks/{task_id}/

    AsyncResult 会去 Redis（result backend）里读这个任务的状态：
    PENDING  -> 排队中/还没开始
    STARTED  -> 正在执行
    SUCCESS  -> 成功，result 里是返回值
    FAILURE  -> 失败，result 里是异常信息
    """

    def get(self, request, task_id):
        result = AsyncResult(task_id)
        payload = {"task_id": task_id, "status": result.status}

        if result.successful():
            # 任务成功，把结果一起返回
            payload["result"] = result.result
        elif result.failed():
            # 任务失败，返回错误信息（转成字符串方便前端显示）
            payload["error"] = str(result.result)

        return Response(payload)
