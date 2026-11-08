"""
core/views.py —— 视图层（View）

# ==========================================================================
# 一、视图在整个请求链路中的位置
# ==========================================================================
# 浏览器 / 前端
#      │  GET /api/notes/?search=django
#      ▼
# config/urls.py ──► core/urls.py ──► 找到 NoteViewSet
#      │
#      ▼
# 视图（本文件）   ← 你在这里写业务逻辑
#      │  用 Serializer 把对象转成 dict
#      ▼
# Response ──► DRF 渲染成 JSON ──► 浏览器
#
# 一句话：URL 决定「谁来处理」，视图决定「怎么处理」。
#
# ==========================================================================
# 二、本项目用了两种视图，务必分清
# ==========================================================================
# 1) APIView（最基础）
#      自己写 get() / post() 方法，灵活但啰嗦。
#      本文件的 HealthView / AddTaskView / SlowTaskView / TaskStatusView 用它。
#
# 2) ModelViewSet（DRF 全家桶）
#      一个类自动拥有 list / create / retrieve / update / partial_update / destroy
#      6 个动作，配合 router 自动生成 6 条路由。
#      本文件的 NoteViewSet 用它，所以看不到任何 CRUD 代码。
#
#       路由生成规则（router.register("notes", NoteViewSet)）：
#         GET    /api/notes/           -> list          （列表 + 分页 + 搜索）
#         POST   /api/notes/           -> create        （新增）
#         GET    /api/notes/1/         -> retrieve      （详情）
#         PUT    /api/notes/1/         -> update        （全量更新）
#         PATCH  /api/notes/1/         -> partial_update（局部更新）
#         DELETE /api/notes/1/         -> destroy       （删除）
#
# ==========================================================================
# 三、DRF 的 Response 和 Django 原生 HttpResponse 有什么区别？
# ==========================================================================
# HttpResponse     : 你得自己 json.dumps()，还要自己设 Content-Type。
# rest_framework.response.Response:
#       - 直接传 Python 字典/列表，DRF 自动转 JSON；
#       - 自动处理中文（不会转成 \\u4e2d）；
#       - 会根据请求头里的 Accept 自动选渲染器（浏览器里还能看到可视化页面）。
# ==========================================================================
"""

# Celery 官方提供的「任务结果查询器」。
# 给它一个 task_id，它就去 Redis（result backend）里读这个任务的状态和返回值。
from celery.result import AsyncResult

# Django 的缓存统一入口（本项目后端是 Redis，配置见 settings.CACHES）。
# 用 cache.xxx 而不是直接 import redis，好处是：以后换成 Memcached
# 只需要改 settings，业务代码一个字都不用动。
from django.core.cache import cache

# connection 代表「当前线程的数据库连接」。
# 它默认是懒加载的：只有真正执行 SQL 时才建立连接。
# ensure_connection() 强制立刻连一次，正好可以用来做健康检查。
from django.db import connection

# rest_framework.status 是一堆语义化的 HTTP 状态码常量，
# 用 status.HTTP_200_OK 比裸写 200 更易读、更不容易写错。
from rest_framework import status, viewsets

# Response 是 DRF 的响应类，传字典就行，自动变 JSON。
from rest_framework.response import Response

# APIView 是所有 DRF 视图的基类，适合写「非标准 CRUD」的接口。
from rest_framework.views import APIView

# 本 app 的模型和序列化器
from .models import Note
from .serializers import NoteSerializer

# 本 app 的 Celery 任务。注意这里 import 的是「任务函数对象」，
# 它已经被 @shared_task 包装过，所以才有 .delay() 方法。
from .tasks import add, slow_task


class HealthView(APIView):
    """健康检查接口：GET /api/health/

    【它解决什么问题】
    前端 / 运维 / 监控系统需要知道「后端到底活着没」。
    但「Django 进程活着」不代表「能用」——如果 MySQL 挂了、Redis 挂了，
    接口照样全废。所以这个接口会主动去探一下两个依赖。

    【为什么用 APIView 而不是 ViewSet】
    健康检查不是对某张表的 CRUD，没有「资源」的概念，
    用最朴素的 APIView 写一个 get() 最直观。

    【返回什么】
        {"status": "ok",       "db": true,  "redis": true}   200
        {"status": "degraded", "db": false, "redis": true}   503
    """

    def get(self, request):
        """处理 GET 请求。方法名必须是 get（小写），DRF 会自动按 HTTP 方法分发。"""

        # ------------------------------------------------------------------
        # 第一步：检查 MySQL 是否连得上
        # ------------------------------------------------------------------
        # connection.ensure_connection()：
        #   - 如果当前还没连数据库，就立刻发起一次连接；
        #   - 如果已经连上了，就什么也不做（零成本）。
        #
        # ★ 为什么必须包 try/except？
        #   数据库连不上时它会抛 OperationalError，如果不捕获，
        #   整个健康检查接口自己就 500 了——那还检查个啥。
        #   我们要的是「优雅地报告故障」，而不是「跟着一起崩」。
        #
        # ★ 这里 catch 的是 Exception 而不是具体的 OperationalError，
        #   因为不同数据库驱动的异常类型不完全一样，健康检查只关心「成不成」。
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            db_ok = False

        # ------------------------------------------------------------------
        # 第二步：检查 Redis 是否可用
        # ------------------------------------------------------------------
        # 思路：写一个值进去，再读出来比对。
        #   - 写成功 + 读回来一样  ->  Redis 正常；
        #   - 任何一步抛异常        ->  Redis 挂了。
        #
        # ★ 为什么不直接用 ping()？
        #   因为 cache 是 Django 的抽象层，它不保证底层一定提供 ping；
        #   用「写-读」验证才和真实业务用法一致（业务也是这么用缓存的）。
        #
        # timeout=10：这个 key 10 秒后自动消失。
        # ★ 一定要设过期时间！否则每 10 秒一次的健康检查会在 Redis 里
        #   留下永久垃圾键（虽然只有一个 key，但习惯要从这里养成）。
        try:
            cache.set("health", "ok", timeout=10)
            redis_ok = cache.get("health") == "ok"
        except Exception:
            redis_ok = False

        # ------------------------------------------------------------------
        # 第三步：汇总结果
        # ------------------------------------------------------------------
        # 只有两个依赖都正常才算 ok，否则统一叫 degraded（降级：还能跑但功能受损）
        status_text = "ok" if db_ok and redis_ok else "degraded"

        return Response(
            # 返回体里把每个依赖的明细都带上，方便前端/运维定位到底是哪个挂了
            {"status": status_text, "db": db_ok, "redis": redis_ok},

            # ★ 状态码为什么是 503 而不是 500？
            #   500 = 代码有 bug（未捕获异常）；
            #   503 = 服务暂时不可用（依赖挂了、维护中）。
            #   健康检查失败属于后者。监控工具（K8s、Nginx upstream_check 等）
            #   正是靠 503 来判断「这台机器该摘掉了」。
            status=status.HTTP_200_OK if status_text == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class NoteViewSet(viewsets.ModelViewSet):
    """笔记的完整 CRUD：增、删、改、查、搜索、分页、排序。

    【这个类为什么这么短？】
    因为 ModelViewSet 已经把 6 个动作全写好了，我们只需要告诉它三件事：
        1. 查哪些数据   -> queryset
        2. 怎么转 JSON  -> serializer_class
        3. 怎么搜/怎么排 -> search_fields / ordering_fields / ordering

    【自动获得的 6 个接口】（配合 core/urls.py 里的 router）
        GET    /api/notes/?search=关键词&page=1       列表（分页 + 搜索）
        POST   /api/notes/                            新增
        GET    /api/notes/{id}/                       详情
        PUT    /api/notes/{id}/                       全量更新
        PATCH  /api/notes/{id}/                       局部更新
        DELETE /api/notes/{id}/                       删除

    【如果哪天要自定义某个动作】
    在类里写 def list(self, request): ... 就能覆盖默认的列表逻辑，
    其他动作不受影响（这也是「多继承 + Mixin」设计的好处）。
    """

    # ---- 数据来源 ----
    # Note.objects.all() 等价于 SELECT * FROM core_note。
    # ★ queryset 写成类的属性（而不是每次请求现算），Django 会做惰性求值：
    #   这里其实还没有执行 SQL，真正查询发生在视图内部调 .all() / 分页切片时。
    queryset = Note.objects.all()

    # ---- 序列化器 ----
    # 增删改查都会用它：读的时候转 JSON，写的时候校验 + 建对象。
    serializer_class = NoteSerializer

    # ---- 搜索 ----
    # 前端传 ?search=xxx 时，DRF 会在这些字段里做 SQL 的 LIKE '%xxx%' 查询。
    # 即 icontains（i = 不区分大小写）：
    #   WHERE title LIKE '%xxx%' OR content LIKE '%xxx%'
    #
    # ★ 这里之所以能生效，是因为 settings.REST_FRAMEWORK 里配了
    #   DEFAULT_FILTER_BACKENDS 包含 SearchFilter。
    #   少配了它，search_fields 写了也没用（这个坑非常常见）。
    search_fields = ["title", "content"]

    # ---- 排序 ----
    # 允许前端用 ?ordering=created_at / ?ordering=-created_at / ?ordering=title
    # 白名单机制：没列在这里的字段就算传了也不让排（防止恶意的 ORDER BY 注入）。
    ordering_fields = ["id", "created_at", "title"]

    # 前端不传 ordering 时的默认排序，-id 表示按 id 倒序（最新在前）。
    ordering = ["-id"]

    # ---- 分页 ----
    # 分页已经在 settings.REST_FRAMEWORK 里全局配置好了（每页 5 条），
    # 返回格式是 {"count": 12, "next": "...?page=2", "previous": null, "results": [...]}。
    #
    # 如果只想给这个接口单独设每页条数，取消下面两行注释即可：
    # pagination_class = PageNumberPagination
    # pagination_class.page_size = 5
    #
    # 反过来，如果想让某个接口不分页（直接返回数组），写：
    # pagination_class = None


class AddTaskView(APIView):
    """提交一个 Celery 加法任务：POST /api/tasks/add/

    【为什么这个接口不直接返回 a+b 的结果？】
    为了演示「异步」。这里故意绕一圈：
        请求进来 -> 丢进 Redis 队列 -> 立刻返回 task_id -> 用户拿 id 去轮询结果
    逻辑上确实多此一举，但这正是处理「慢任务」的标准套路：
        发邮件、生成报表、调用第三方 API 都可以套这个模板。

    【请求】 {"a": 7, "b": 35}
    【响应】 {"task_id": "3f2a..."}  HTTP 202
    """

    def post(self, request):
        """处理 POST 请求。"""

        # request.data 是 DRF 帮我们解析好的请求体：
        #   Content-Type: application/json  -> 直接变成 dict
        #   Content-Type: form-data         -> 变成 QueryDict（类似 dict）
        #
        # ★ 为什么套 int()？
        #   JSON 里 {"a": "7"} 传字符串也很常见（前端 input 拿到的都是字符串）。
        #   int() 既能容错 "7"，又能在传 "abc" 时抛 ValueError 被下面捕获。
        #
        # .get("a", 0)：没传这个键时给个默认值 0，避免 KeyError。
        try:
            a = int(request.data.get("a", 0))
            b = int(request.data.get("b", 0))
        except (TypeError, ValueError):
            # TypeError  -> 传了 null，int(None) 会炸
            # ValueError -> 传了 "abc"，int("abc") 会炸
            # 400 Bad Request：客户端的问题，不是服务器的错
            return Response({"detail": "a 和 b 必须是整数"}, status=status.HTTP_400_BAD_REQUEST)

        # ★★★ 整个 Celery 的核心就在这一行 .delay() ★★★
        #
        # add(7, 35)        -> 在当前进程里立刻算，阻塞等到结果返回（同步）；
        # add.delay(7, 35)  -> 只把「参数 7,35」序列化后塞进 Redis 的队列，
        #                      立刻返回一个 AsyncResult 对象（异步）。
        #
        # 真正的闭包计算由另一个进程 celery worker 在后台完成，
        # worker 算完后把结果写回 Redis（result backend）。
        #
        # ★ 如果 worker 没启动：任务会一直躺在队列里，
        #   查状态永远是 PENDING，不是「失败」哦，是「没人干」。
        task = add.delay(a, b)

        # HTTP 202 Accepted：表示「服务器已接收请求，但还没处理完」。
        # 对比一下：
        #   200 OK        -> 事情已经做完了，body 就是结果；
        #   201 Created   -> 新建了资源（比如 POST 一条笔记）；
        #   202 Accepted  -> 收到活儿了，处理中，你去别的接口查进度。
        # 用 202 才是最符合异步语义的写法。
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class SlowTaskView(APIView):
    """提交一个 Celery 耗时任务：POST /api/tasks/slow/

    【用来体验什么】
    「接口秒回、任务后台跑」。前端调用后会立刻拿到 task_id，
    可以一边等待一边继续操作页面（配合 TaskStatusView 轮询）。

    【请求】 {"seconds": 5}
    【响应】 {"task_id": "..."}  HTTP 202
    """

    def post(self, request):
        # 默认 3 秒。★ 这里没做 try/except int()，
        # 因为这是演示接口；真实项目请照 AddTaskView 那样加上校验，
        # 否则传 "abc" 会直接 500。
        seconds = int(request.data.get("seconds", 3))

        # 丢进队列，立刻返回
        task = slow_task.delay(seconds)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)


class TaskStatusView(APIView):
    """查询 Celery 任务的状态和结果：GET /api/tasks/{task_id}/

    【典型用法：轮询】
    前端拿到 task_id 后，每隔 1~2 秒调一次这个接口，
    直到 status 变成 SUCCESS 或 FAILURE 就停止轮询。

    【AsyncResult 是什么】
    Celery 提供的「任务句柄」。只给它 task_id 就能去 Redis 里查状态，
    注意：它不依赖当前进程，所以换一台机器也能查。

    【四种状态的完整生命周期】
        PENDING  -> 任务在队列里排队，或 worker 还没取到（★ 也可能是 task_id 根本不存在）
        STARTED  -> worker 正在执行（需要 CELERY_TASK_TRACK_STARTED=True 才有这个状态）
        SUCCESS  -> 成功，result.result 是函数的返回值
        FAILURE  -> 失败，result.result 是异常对象（不是字符串！）
    """

    def get(self, request, task_id):
        # task_id 从 URL 里来：core/urls.py 的 <str:task_id> 捕获后自动传进来。
        # ★ 视图方法的参数名必须和 URL 里的变量名完全一致，否则 Django 报 TypeError。
        result = AsyncResult(task_id)

        # 先把「一定有的信息」装好
        payload = {"task_id": task_id, "status": result.status}

        # ---- 成功：把返回值带上 ----
        # result.successful() 判断 status == SUCCESS。
        # result.result：任务函数的返回值（这里是 int 或 str，可以放心 JSON 序列化）。
        if result.successful():
            payload["result"] = result.result

        # ---- 失败：把错误信息带上 ----
        # ★ 注意 result.result 在失败时是「异常对象」，直接丢给 JSON 会序列化失败，
        #   所以必须 str() 一下转成字符串，比如 "division by zero"。
        #   这也意味着前端拿到的是「错误的文字描述」，不是结构化的异常。
        elif result.failed():
            payload["error"] = str(result.result)

        # ★ 状态默认是 200：因为「查询动作本身成功了」，
        #   哪怕任务失败了，这个查询请求也是成功的（类似 HTTP 没有问题）。
        #   如果你想让任务失败时返回 500，可以改成：
        #   status=500 if result.failed() else 200
        return Response(payload)
