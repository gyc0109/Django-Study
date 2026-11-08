"""视图（View）—— 接口的具体逻辑。

本次练习用到三类视图：
    1. APIView       ：最基础，自己写 get/post（健康检查、任务接口）
    2. ModelViewSet  ：DRF 全家桶，自动拥有增删改查（分类、图书）
    3. Mixin         ：把多个视图共用的逻辑抽出来（列表缓存失效）

列表缓存采用「版本号」思路：
    每次写操作（增/改/删）就把版本号换成一个新的时间戳，
    列表缓存的 key 里带着版本号，旧 key 自然不会再被读到，
    30 秒后自动过期。这样不用去 Redis 里模糊删除一大堆 key。
"""

import time

from celery.result import AsyncResult
from django.core.cache import cache
from django.db import connection
from django.db.models import ProtectedError
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Category
from .serializers import BookSerializer, CategorySerializer
from .tasks import generate_stock_report

# 缓存版本号在 Redis 里的 key
CACHE_VERSION_KEY = "library:cache_version"
# 列表缓存保留时间（秒）
LIST_CACHE_TIMEOUT = 30


def get_cache_version():
    """读取当前缓存版本；没有就初始化一个时间戳。"""
    version = cache.get(CACHE_VERSION_KEY)
    if version is None:
        version = time.time_ns()
        cache.set(CACHE_VERSION_KEY, version, timeout=None)
    return version


def bump_cache_version():
    """让所有旧的列表缓存立即失效。

    用时间戳当版本号，天然不会重复，也不需要自增计数器的并发处理。
    """
    cache.set(CACHE_VERSION_KEY, time.time_ns(), timeout=None)


def build_cache_key(prefix, request):
    """拼出唯一的缓存 key，例如 library:books:1700000000:/api/books/?page=1。"""
    return f"library:{prefix}:{get_cache_version()}:{request.get_full_path()}"


class CachedListMixin:
    """给 ViewSet 的列表接口加 Redis 缓存，并在写操作后自动失效。

    子类只需要设置：
        cache_prefix  = "books" / "categories"
    """

    cache_prefix = "list"

    def list(self, request, *args, **kwargs):
        key = build_cache_key(self.cache_prefix, request)
        cached = cache.get(key)
        if cached is not None:
            # 命中缓存：直接返回，不再查 MySQL
            return Response(cached)

        # 没命中：走 DRF 默认逻辑查数据库
        response = super().list(request, *args, **kwargs)
        # response.data 有两种形态，直接整体缓存即可：
        #   开启分页 -> {"count": ..., "results": [...]}
        #   关闭分页 -> [ {...}, {...} ]（例如 CategoryViewSet）
        # 注意不能套 dict()，否则遇到列表会报 ValueError。
        cache.set(key, response.data, timeout=LIST_CACHE_TIMEOUT)
        return response

    def perform_create(self, serializer):
        serializer.save()
        bump_cache_version()

    def perform_update(self, serializer):
        serializer.save()
        bump_cache_version()

    def perform_destroy(self, instance):
        instance.delete()
        bump_cache_version()


class HealthView(APIView):
    """GET /api/health/ —— 检查 Django、MySQL、Redis 是否都正常。"""

    def get(self, request):
        # 检查 MySQL：真正尝试建立一次连接
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False

        # 检查 Redis：写一个值再读出来
        try:
            cache.set("library:health", "ok", timeout=10)
            redis_ok = cache.get("library:health") == "ok"
        except Exception:
            redis_ok = False

        status_text = "ok" if db_ok and redis_ok else "degraded"
        return Response(
            {"status": status_text, "db": db_ok, "redis": redis_ok},
            status=(
                status.HTTP_200_OK
                if status_text == "ok"
                else status.HTTP_503_SERVICE_UNAVAILABLE
            ),
        )


class CategoryViewSet(CachedListMixin, viewsets.ModelViewSet):
    """分类的增删改查：/api/categories/

    为什么继承顺序是 CachedListMixin 在前？
        Python 的方法查找顺序（MRO）从左到右，
        这样 list / perform_* 才会优先使用 Mixin 里的版本。
    """

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ["name"]
    ordering_fields = ["id", "name", "created_at"]
    ordering = ["id"]
    cache_prefix = "categories"

    # 分类数量少，前端下拉框需要一次性拿全，
    # 所以单独关掉分页（settings 里的全局分页只影响没关的接口）。
    # 关闭后响应直接是数组，不再是 {count, results} 结构。
    pagination_class = None

    def perform_destroy(self, instance):
        """删除分类前先处理「分类下还有书」的情况。

        模型上外键用了 on_delete=PROTECT，
        直接删会抛 ProtectedError。这里翻译成 400 + 中文提示，
        比让服务器返回 500 更友好。
        """
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError({"detail": "该分类下还有图书，不能删除"})
        bump_cache_version()


class BookViewSet(CachedListMixin, viewsets.ModelViewSet):
    """图书的增删改查：/api/books/

    支持的查询参数：
        ?page=2              分页
        ?search=python       在书名、作者里模糊搜索
        ?category=3          只看某个分类
        ?ordering=-price     排序（价格从高到低）
    """

    serializer_class = BookSerializer
    search_fields = ["title", "author"]
    ordering_fields = ["id", "title", "price", "stock", "created_at"]
    ordering = ["-id"]
    cache_prefix = "books"

    def get_queryset(self):
        # select_related("category")：一次 SQL 把分类也查出来，
        # 避免序列化每本书时再单独查一次分类（N+1 查询问题）
        queryset = Book.objects.select_related("category").all()

        # 按分类筛选
        category_id = self.request.query_params.get("category")
        if category_id:
            try:
                queryset = queryset.filter(category_id=int(category_id))
            except (TypeError, ValueError):
                # 传了非数字就当没有结果，而不是让服务器报 500
                queryset = queryset.none()

        return queryset


class StockReportTaskView(APIView):
    """POST /api/tasks/report/ —— 提交「生成库存报表」异步任务。

    请求体可以为空。
    响应：{"task_id": "..."}，之后拿这个 id 去查结果。
    """

    def post(self, request):
        # .delay() 把任务丢进 Redis 队列，立即返回，不阻塞请求
        task = generate_stock_report.delay()
        # 202 Accepted：已接收，稍后处理
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class TaskStatusView(APIView):
    """GET /api/tasks/{task_id}/ —— 查询任务状态和结果。"""

    def get(self, request, task_id):
        result = AsyncResult(task_id)
        payload = {"task_id": task_id, "status": result.status}

        if result.successful():
            payload["result"] = result.result
        elif result.failed():
            payload["error"] = str(result.result)

        return Response(payload)
