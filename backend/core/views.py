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
    """检查 Django、MySQL、Redis 三方连通性。"""

    def get(self, request):
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False

        try:
            cache.set("health", "ok", timeout=10)
            redis_ok = cache.get("health") == "ok"
        except Exception:
            redis_ok = False

        status_text = "ok" if db_ok and redis_ok else "degraded"
        return Response(
            {"status": status_text, "db": db_ok, "redis": redis_ok},
            status=status.HTTP_200_OK if status_text == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class NoteViewSet(viewsets.ModelViewSet):
    """MySQL CRUD 示例。"""

    queryset = Note.objects.all()
    serializer_class = NoteSerializer


class AddTaskView(APIView):
    """提交一个 Celery 加法任务。"""

    def post(self, request):
        try:
            a = int(request.data.get("a", 0))
            b = int(request.data.get("b", 0))
        except (TypeError, ValueError):
            return Response({"detail": "a 和 b 必须是整数"}, status=status.HTTP_400_BAD_REQUEST)

        task = add.delay(a, b)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class SlowTaskView(APIView):
    """提交一个 Celery 耗时任务。"""

    def post(self, request):
        seconds = int(request.data.get("seconds", 3))
        task = slow_task.delay(seconds)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class TaskStatusView(APIView):
    """查询 Celery 任务状态与结果。"""

    def get(self, request, task_id):
        result = AsyncResult(task_id)
        payload = {"task_id": task_id, "status": result.status}
        if result.successful():
            payload["result"] = result.result
        elif result.failed():
            payload["error"] = str(result.result)
        return Response(payload)
