"""视图（View）—— 接口的具体逻辑。

一个请求的完整旅程：
    浏览器/curl 发请求
      -> Django 根据 URL 找到对应视图
      -> 视图读参数、查数据库、调用任务……
      -> 返回 Response（DRF 自动转成 JSON）
      -> 中间件再处理一遍响应头
      -> 浏览器收到 JSON

本文件用到三类视图：
    1. APIView      ：最基础。自己写 get() / post()，完全掌控流程，
                      适合「不属于某个模型」的接口（健康检查、任务提交）。
    2. ModelViewSet ：DRF 全家桶。声明 queryset + serializer_class，
                      自动拥有 列表/详情/新增/更新/删除 6 个接口。
    3. Mixin        ：把多个视图要复用的逻辑抽出来（这里的列表缓存）。

列表缓存采用「版本号」思路：
    每次写操作（增/改/删）就把版本号换成一个新的时间戳；
    列表缓存的 key 里带着版本号，旧 key 自然不会再被读到，30 秒后自动过期。
    这样不用去 Redis 里模糊删除一大堆 key（SCAN + DEL 既慢又容易误删）。
"""

# time 用来生成「纳秒级时间戳」当作缓存版本号。
# 为什么用时间戳而不是 1、2、3 自增？
#   自增需要「读-改-写」三步，并发时两个请求可能读到同一个值；
#   时间戳天然唯一（纳秒级几乎不会重复），不需要锁。
import time

# Celery 提供的查询工具：根据 task_id 去 Redis 里读任务状态。
from celery.result import AsyncResult
# Django 的缓存门面：cache.get / cache.set，底层就是我们配置的 Redis。
from django.core.cache import cache
# connection 代表「当前数据库连接」，用来做健康检查。
from django.db import connection
# ProtectedError：删除被外键保护的对象时，Django 抛出的异常。
from django.db.models import ProtectedError
# status 里是一堆 HTTP 状态码常量；viewsets 是 ViewSet 的基类集合。
from rest_framework import status, viewsets
# DRF 的 ValidationError：raise 它，DRF 会自动返回 400 + 错误 JSON。
from rest_framework.exceptions import ValidationError
# Response：DRF 的响应类，会把 Python 字典转成 JSON。
from rest_framework.response import Response
# APIView：最基础的类视图。
from rest_framework.views import APIView

# 本 app 的模型和序列化器。
from .models import Book, Category
from .serializers import BookSerializer, CategorySerializer
# 本 app 的 Celery 任务。
from .tasks import generate_stock_report

# ------------------------------------------------------------
# 模块级常量（全大写是 Python 的约定，表示「不要随便改」）
# ------------------------------------------------------------
# 缓存版本号在 Redis 里的 key。
# 实际存进去时 Django 还会加前缀和库号，形如 :1:library:cache_version
CACHE_VERSION_KEY = "library:cache_version"

# 列表缓存保留多少秒。
# 30 秒是「短缓存」：即使版本号机制出问题，最多也只脏 30 秒。
LIST_CACHE_TIMEOUT = 30


def get_cache_version():
    """读取当前的缓存版本号；不存在就初始化一个并返回。

    返回值：
        int 类型的纳秒时间戳（例如 1762600000123456789）。

    为什么 timeout=None？
        版本号本身不能过期，否则过期后列表缓存会「集体失效」，
        缓存的意义就没了。旧版本的 key 会在 30 秒后自然过期。
    """
    # cache.get 在 key 不存在时返回 None（不会报错）。
    version = cache.get(CACHE_VERSION_KEY)
    if version is None:
        # time.time_ns() 返回「从 1970 年到现在经过的纳秒数」。
        # 用它当版本号，几乎不可能和上一次重复。
        version = time.time_ns()
        # timeout=None 表示永不过期（Django 会一直保存这个 key）。
        cache.set(CACHE_VERSION_KEY, version, timeout=None)
    return version


def bump_cache_version():
    """把版本号换成一个新时间戳，让所有旧的列表缓存「立即失效」。

    「失效」的原理不是删除，而是「让旧 key 再也匹配不上」：
        旧：library:books:1700000000:/api/books/?page=1
        新：library:books:1700000123:/api/books/?page=1
    读缓存时用的是新版本号，自然命中不到旧 key；
    旧 key 没人访问，30 秒后自动过期，被 Redis 回收。
    """
    cache.set(CACHE_VERSION_KEY, time.time_ns(), timeout=None)


def build_cache_key(prefix, request):
    """拼出唯一的缓存 key。

    例如：
        library:books:1700000000:/api/books/?page=1&search=Python

    为什么要带上 request.get_full_path()？
        列表接口的结果和「查询参数」强相关：
            ?page=1 和 ?page=2 是两份不同的数据
            ?search=Python 和 ?search=Django 也不一样
        把完整路径（含查询字符串）拼进 key，不同参数自然对应不同缓存，
        不会出现「第 2 页显示第 1 页数据」这种串数据事故。
    """
    return f"library:{prefix}:{get_cache_version()}:{request.get_full_path()}"


class CachedListMixin:
    """给 ViewSet 的「列表接口」加 Redis 缓存，并在写操作后自动让缓存失效。

    Mixin 是什么？
        一个普通的类，专门装「可复用的方法」，自己不单独使用，
        而是和别的类一起被继承（这里和 ModelViewSet 组合）。

    子类只需要设置一个类属性：
        cache_prefix = "books" 或 "categories"
    """

    # 默认前缀：子类不设置时用它（避免拼 key 时 AttributeError）。
    cache_prefix = "list"

    def list(self, request, *args, **kwargs):
        """覆写 DRF 的 list()，在「查数据库」前面加一层缓存判断。"""
        # 1) 先根据「前缀 + 版本号 + 完整路径」算出 key。
        key = build_cache_key(self.cache_prefix, request)

        # 2) 尝试从 Redis 读。
        cached = cache.get(key)
        if cached is not None:
            # 命中缓存：直接把上次存的数据包装成 Response 返回。
            # 这一次完全不查 MySQL，所以速度是「内存级」的。
            return Response(cached)

        # 3) 没命中：调用父类（ModelViewSet）的 list()，正常查数据库、分页、序列化。
        # super().list(...) 会根据 MRO 找到 ModelViewSet.list。
        response = super().list(request, *args, **kwargs)

        # 4) 把结果写回 Redis，下次同样的请求就能直接命中。
        # response.data 有两种形态，直接整体缓存即可：
        #   开启分页   -> {"count": 12, "next": ..., "results": [...]}
        #   关闭分页   -> [{...}, {...}]（例如 CategoryViewSet）
        # 注意：不能套 dict()，否则遇到列表会抛 ValueError。
        cache.set(key, response.data, timeout=LIST_CACHE_TIMEOUT)
        return response

    # ------------------------------------------------------------
    # 下面三个方法是 DRF 的「钩子」：
    #   perform_create / perform_update / perform_destroy
    # 分别在「新增 / 更新 / 删除」真正落库时被调用。
    # 我们在这里加一行「让缓存失效」，保证写完立刻能读到新数据。
    # ------------------------------------------------------------
    def perform_create(self, serializer):
        """新增成功后，旧列表缓存必须作废。"""
        # serializer.save() 才是真正执行 INSERT 的那一步。
        # 不调用它，数据不会进数据库（DRF 不会自动帮你调）。
        serializer.save()
        bump_cache_version()

    def perform_update(self, serializer):
        """更新成功后，旧列表缓存必须作废。"""
        serializer.save()
        bump_cache_version()

    def perform_destroy(self, instance):
        """删除成功后，旧列表缓存必须作废。"""
        # instance 是要删除的那条记录对象。
        instance.delete()
        bump_cache_version()


class HealthView(APIView):
    """GET /api/health/ —— 检查 Django、MySQL、Redis 是否都正常。

    为什么需要健康检查？
        线上服务出问题时，第一件事是确认「哪个依赖挂了」。
        这个接口一次告诉你三件事：Django 活着、MySQL 能连、Redis 能读写。
        监控系统可以定时请求它，返回 503 就报警。
    """

    def get(self, request):
        """处理 GET 请求。

        APIView 的规则：
            请求方法是 GET 就调用 get()，是 POST 就调用 post()；
            没定义对应方法时，DRF 自动返回 405 Method Not Allowed。
        """
        # --------------------------------------------------------
        # 1) 检查 MySQL
        # connection.ensure_connection() 会尝试真正建立一次数据库连接。
        # 注意：普通查询可能走连接池/复用连接，健康检查要的是「现在能不能连」。
        # 连不上会抛异常，所以必须 try/except，否则整个接口直接 500。
        # 这里捕获 Exception 是故意的：健康检查不应该因为任何数据库错误而崩溃。
        # --------------------------------------------------------
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False

        # --------------------------------------------------------
        # 2) 检查 Redis
        # 思路：写一个值，再读回来，值对得上才算正常。
        # 只 ping 也能测连通性，但「读写都成功」更能证明缓存真的可用。
        # timeout=10：10 秒后自动删除，不在 Redis 里留垃圾。
        # --------------------------------------------------------
        try:
            cache.set("library:health", "ok", timeout=10)
            redis_ok = cache.get("library:health") == "ok"
        except Exception:
            redis_ok = False

        # 3) 两个依赖都正常才算 ok，否则是 degraded（降级：服务活着但功能不全）。
        status_text = "ok" if db_ok and redis_ok else "degraded"

        # 4) 正常返回 200，异常返回 503（Service Unavailable）。
        # 用状态码而不是只靠 JSON 里的字段，监控工具/负载均衡才能自动判断。
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

    继承顺序为什么是 CachedListMixin 在前？
        Python 查找方法时按 MRO（方法解析顺序）从左往右找。
        CachedListMixin 在前，它的 list() / perform_* 才会「盖住」
        ModelViewSet 里的同名方法；反过来写，缓存就永远不生效。
    """

    # ------------------------------------------------------------
    # 这 4 个是 ModelViewSet 的「开关」，声明完 6 个接口就自动有了。
    # ------------------------------------------------------------
    # 查哪些数据：等价于 SELECT * FROM library_category
    queryset = Category.objects.all()

    # 用哪个序列化器：负责「对象 <-> JSON」的转换
    serializer_class = CategorySerializer

    # ?search=xxx 会在 name 字段里做模糊匹配（不区分大小写，底层 LIKE %xxx%）
    search_fields = ["name"]

    # 允许 ?ordering=name / ?ordering=-created_at 这样的排序参数
    ordering_fields = ["id", "name", "created_at"]

    # 不传 ordering 时的默认排序（和模型 Meta.ordering 一致）
    ordering = ["id"]

    # 缓存 key 的前缀，最终形如 library:categories:版本号:/api/categories/
    cache_prefix = "categories"

    # ------------------------------------------------------------
    # 分类数量少，前端下拉框需要「一次性拿全」，
    # 所以单独关掉分页（settings 里的全局分页只影响没关的接口）。
    # 关闭后响应直接是数组：[{...}, {...}]，不再是 {count, results} 结构。
    # 这也是 CachedListMixin 里强调「不能套 dict()」的原因。
    # ------------------------------------------------------------
    pagination_class = None

    def perform_destroy(self, instance):
        """删除分类前，先处理「分类下还有书」的情况。

        模型上外键用了 on_delete=PROTECT：
            直接删除时 Django 会先检查有没有关联数据，
            有就抛 ProtectedError（数据库层面会拒绝删除）。
        这里把它翻译成 400 + 中文提示，
        比让服务器返回 500 Internal Server Error 更友好、更准确。
        """
        try:
            instance.delete()
        except ProtectedError:
            # ValidationError 里传字典，DRF 会把内容原样放进响应体：
            #   {"detail": "该分类下还有图书，不能删除"}
            raise ValidationError({"detail": "该分类下还有图书，不能删除"})

        # 删除成功后才让缓存失效。
        # 注意：如果上面 raise 了，这行不会执行（异常会直接向上抛），
        # 也就不会无意义地刷新版本号。
        bump_cache_version()


class BookViewSet(CachedListMixin, viewsets.ModelViewSet):
    """图书的增删改查：/api/books/

    支持的查询参数（可以组合使用）：
        ?page=2              分页，每页 5 条
        ?search=python       在书名、作者里模糊搜索
        ?category=3          只看某个分类
        ?ordering=-price     排序（价格从高到低）
    """

    serializer_class = BookSerializer

    # 搜索范围：书名 + 作者。
    # SearchFilter 默认用 icontains（不区分大小写的包含匹配），
    # 由数据库执行，不会把全部数据查到 Python 里再过滤。
    search_fields = ["title", "author"]

    # 允许排序的字段清单。
    # 不在这个列表里的字段，?ordering=xxx 会被忽略（防止乱传字段拖慢数据库）。
    ordering_fields = ["id", "title", "price", "stock", "created_at"]

    # 默认最新在前。
    ordering = ["-id"]

    cache_prefix = "books"

    def get_queryset(self):
        """动态返回本次请求要查询的数据集。

        为什么不用类属性 queryset，而要写方法？
            因为「按分类筛选」依赖本次请求的参数（self.request），
            类属性在服务启动时就固定了，拿不到请求信息。
            DRF 每次处理请求都会调用 get_queryset()。
        """
        # select_related("category")：
        #   让 Django 用一条 SQL 把 book 和它的 category 一起查出来（JOIN）。
        #   如果不加，序列化每本书时访问 book.category.name 都会再查一次数据库，
        #   12 本书就是 1 + 12 = 13 条 SQL，这就是著名的 N+1 查询问题。
        queryset = Book.objects.select_related("category").all()

        # 读取查询参数 ?category=3（不存在时返回 None）。
        category_id = self.request.query_params.get("category")
        if category_id:
            try:
                # 手动转 int 再过滤：
                # 好处是传 "abc" 时能进 except，而不是让数据库报错。
                queryset = queryset.filter(category_id=int(category_id))
            except (TypeError, ValueError):
                # 传了非数字：返回「空结果集」，而不是 500。
                # cause: ?category=abc 是用户输入错误，不是服务器故障。
                queryset = queryset.none()

        return queryset


class StockReportTaskView(APIView):
    """POST /api/tasks/report/ —— 提交「生成库存报表」异步任务。

    请求体可以为空（不需要任何参数）。
    响应：{"task_id": "xxxx"}，之后拿这个 id 去 /api/tasks/{task_id}/ 查结果。

    为什么用 POST 而不是 GET？
        这个接口会「创建」一个任务（有副作用、会改变服务器状态），
        按 REST 语义应该用 POST；GET 只用来读取数据。
    """

    def post(self, request):
        # .delay() 是关键：
        #   把任务序列化后丢进 Redis 队列（broker），立刻返回一个 AsyncResult 对象。
        #   真正的计算由另一个终端里的 celery worker 完成。
        #   如果写成 generate_stock_report()（不带 .delay），
        #   请求会在这里阻塞 2 秒，异步就完全失去意义了。
        task = generate_stock_report.delay()

        # 202 Accepted：服务器已接收请求，但还没处理完。
        # 比 200 OK 更准确——200 意味着「事情已经做完了」，而这里并没有。
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class TaskStatusView(APIView):
    """GET /api/tasks/{task_id}/ —— 查询任务状态和结果。

    task_id 是 Celery 生成的一个 UUID 字符串（例如 096447e3-...）。
    前端拿到它后，每隔几百毫秒来问一次，直到状态变成 SUCCESS 或 FAILURE。
    """

    def get(self, request, task_id):
        # AsyncResult 会去 Redis（result backend）里按 id 读取这条任务的记录。
        result = AsyncResult(task_id)

        # 先放两个「任何状态都有的」字段。
        # result.status 的常见值：
        #   PENDING  -> 排队中，或 id 根本不存在（Celery 无法区分这两种情况）
        #   STARTED  -> 正在执行（需要 CELERY_TASK_TRACK_STARTED=True 才会出现）
        #   SUCCESS  -> 成功，result.result 是任务返回值
        #   FAILURE  -> 失败，result.result 是异常对象
        payload = {"task_id": task_id, "status": result.status}

        if result.successful():
            # 任务成功：把返回值一起给前端。
            # 本项目返回值是 {"total_titles": ..., "total_stock": ..., "total_value": ...}
            payload["result"] = result.result
        elif result.failed():
            # 任务失败：把异常转成字符串，方便前端直接显示。
            # 注意不要把完整 traceback 暴露给生产环境（可能泄露代码结构）。
            payload["error"] = str(result.result)

        # 无论成功失败，HTTP 状态码都是 200：
        # 「查询任务状态」这个动作本身成功了，任务失败是业务结果，不是接口故障。
        return Response(payload)
