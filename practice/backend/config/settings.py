"""
练习项目「图书管理」的全局配置文件（settings.py）。

===============================================================================
一、这个文件是什么？
===============================================================================
它是整个 Django 项目的「总控制台」。你新建项目后，Django 默认生成一个
settings.py，里面配好了几十项默认值；我们要改的只是其中一小部分：

    - 数据库换成 MySQL
    - 缓存换成 Redis
    - 装上 DRF（写接口）和 CORS（跨域）
    - 配置 Celery（异步任务）

Django 启动时第一件事就是执行这个文件，把里面的变量读进内存，
所以这里写错了，整个项目都起不来。

===============================================================================
二、为什么有 os.getenv / .env？
===============================================================================
密码、密钥这类东西不应该硬编码在代码里（尤其是要传到 GitHub 的时候）。
标准做法是：
    代码里写 os.getenv("XXX", "默认值")  →  真正的值放在 .env 文件里
.gitignore 里把 .env 忽略掉，仓库里就不会出现密码。

这样做还有个好处：部署到服务器时不用改代码，只改服务器的环境变量即可。

===============================================================================
三、阅读顺序（和真实开发时的思考顺序一致）
===============================================================================
    1. BASE_DIR / .env          项目根目录在哪、敏感配置从哪来
    2. INSTALLED_APPS           启用了哪些功能模块
    3. MIDDLEWARE               每个请求要经过哪些「关卡」
    4. DATABASES / CACHES       数据存哪里（MySQL / Redis）
    5. REST_FRAMEWORK           接口的分页、搜索、权限
    6. CORS_ALLOWED_ORIGINS     允许哪个前端地址跨域访问
    7. CELERY_*                 异步任务队列怎么连 Redis
"""

# =============================================================================
# 0. 导入：标准库 + 第三方库
# =============================================================================
# os：用来读环境变量（os.getenv），这是 Python 标准库
import os
# Path：面向对象的路径操作工具，比字符串拼接更安全（跨操作系统不用关心 / 还是 \）
from pathlib import Path

# python-dotenv 提供的函数：把 .env 文件里的键值对塞进环境变量
from dotenv import load_dotenv

# =============================================================================
# 1. 基础路径与敏感配置（密钥、调试开关）
# =============================================================================
# __file__          当前文件路径 = .../practice/backend/config/settings.py
# .resolve()        转成绝对路径（把 .. 之类的相对符号解析掉）
# .parent           上一级目录 = .../practice/backend/config/
# .parent.parent    再上一级 = .../practice/backend/   ← 这就是 BASE_DIR
#
# 为什么要有 BASE_DIR？
#   项目里所有「相对路径」都以它为基准，比如静态文件目录、媒体文件目录。
#   用了它以后，不管你在哪个目录下敲命令，路径都能算对。
BASE_DIR = Path(__file__).resolve().parent.parent

# 读取 backend/.env 文件。
# 如果文件不存在，load_dotenv 不会报错，只是什么也不做（所以下面都写了默认值）。
# 这也是为什么即使你没建 .env，项目依然能跑起来。
load_dotenv(BASE_DIR / ".env")

# SECRET_KEY：Django 用来做加密签名的密钥。
#   - session 的签名、密码重置链接的签名、CSRF token 都依赖它
#   - 一旦泄露，别人可以伪造登录态，所以生产环境绝不能公开
# 这里的默认值是「故意写成不安全的样子」，一眼就能看出这是开发环境。
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "practice-insecure-key-change-me")

# DEBUG：调试开关。
#   1 / True  ：出错时页面展示完整堆栈，还自动提供静态文件服务（开发方便）
#   0 / False ：出错只回一句 Server Error，堆栈不泄露给用户（上线必须关）
# 注意 os.getenv 读回来永远是字符串，所以要跟字符串 "1" 比较，
# 不能写成 == 1 或者直接 if os.getenv(...)。
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

# ALLOWED_HOSTS：允许用哪些域名/IP 访问本项目。
#   "*.example.com" 通配子域名；["*"] 表示完全不限制。
#   本地学习用 "*" 最省事；上线必须写真实域名，
#   否则会有「域名劫持」风险（攻击者把域名解析到你的服务器）。
ALLOWED_HOSTS = ["*"]

# =============================================================================
# 2. INSTALLED_APPS：启用了哪些功能模块
# =============================================================================
# 每装一个 app，Django 才会：
#   - 加载它的 models（建表）
#   - 加载它的 migrations（数据库迁移）
#   - 加载它的 templates（模板）
#   - 加载它的 management commands（自定义命令，如 seed_demo）
#
# 前 6 个是 Django 自带的核心功能，几乎每个项目都要：
#   admin       后台管理界面
#   auth        用户与权限
#   contenttypes 通用模型类型（auth 依赖它）
#   sessions    会话（session），登录态靠它
#   messages    一次性提示消息（如「保存成功」）
#   staticfiles 静态文件收集
#
# 最后 3 个是本项目额外安装的：
#   rest_framework  DRF：把 model 快速变成 REST API
#   corsheaders     处理跨域（浏览器的同源策略限制）
#   library         我们自己写的业务 app（书、分类）
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "library",
]

# =============================================================================
# 3. MIDDLEWARE：中间件（请求的「关卡」）
# =============================================================================
# 一个 HTTP 请求进来后的流向：
#   浏览器 → 中间件1 → 中间件2 → ... → 视图函数 → ... → 中间件2 → 中间件1 → 浏览器
# 也就是「请求从上往下，响应从下往上」，像洋葱一样一层层包裹。
#
# 顺序很重要，下面逐个说明：
MIDDLEWARE = [
    # 【必须靠前】跨域中间件。
    # 浏览器发跨域「非简单请求」（如 PUT/DELETE、带 JSON 的 POST）前，
    # 会先发一个 OPTIONS 预检请求，问「你允许我这样请求吗」。
    # 如果 CORS 中间件排在很后面，预检请求可能在更前面的关卡就被拒了，
    # 所以官方建议放在尽量靠前（但在 SecurityMiddleware 之后也行）。
    "corsheaders.middleware.CorsMiddleware",

    # 安全相关：HTTPS 重定向、HSTS 等。开发环境基本不生效。
    "django.middleware.security.SecurityMiddleware",

    # 会话：根据 cookie 里的 sessionid 找到服务端 session，注入 request.session
    "django.contrib.sessions.middleware.SessionMiddleware",

    # 通用功能：处理 APPEND_SLASH（自动补结尾斜杠）、ETag 等。
    #
    # ★ 反直觉的坑：APPEND_SLASH 对 GET 是 301 重定向（浏览器会自动跟随），
    #   但对 POST/PUT/DELETE 直接返回 500 RuntimeError！
    #   也就是说调接口时请求路径少写结尾的 "/"：
    #       POST /api/books     → 500  （DRF 路由都是 /api/books/）
    #       GET  /api/books     → 301  → 自动跳转到 /api/books/，看起来「没事」
    #   所以：写前端/curl/Postman 时，路径结尾的 "/" 一定要带上。
    "django.middleware.common.CommonMiddleware",

    # CSRF 防护：防止别的网站冒用你的登录态提交表单。
    # DRF 的 APIView/ViewSet 默认不校验 CSRF（因为通常用 token 认证而不是 cookie），
    # 所以它对接口基本无影响，主要保护 admin 表单。
    "django.middleware.csrf.CsrfViewMiddleware",

    # 认证：根据 session 或 token 确定 request.user 是谁
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # 消息框架：让「保存成功」这类一次性提示能跨请求传递
    "django.contrib.messages.middleware.MessageMiddleware",

    # 防止页面被别的网站用 iframe 嵌套（点击劫持攻击）
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# 总路由文件的位置。写成「包名.模块名」，Django 用 importlib 去导入它。
# 注意是 config.urls，而不是 urls（因为 config 才是一个包）。
ROOT_URLCONF = "config.urls"

# =============================================================================
# 4. TEMPLATES：模板引擎
# =============================================================================
# 我们这个项目主要是给 Vue 前端提供 JSON 接口，几乎不用 Django 模板。
# 但 admin 后台是用模板渲染的，所以这段不能删。
#
#   BACKEND    用哪个模板引擎（Django 自带 DTL）
#   DIRS       额外的模板目录（一般放项目级 templates/，这里是空）
#   APP_DIRS   True = 自动去每个 app 下的 templates/ 目录找模板
#   context_processors  往每个模板上下文里自动注入的变量
#       debug     注入 debug 和 sql_queries
#       request   注入 request 对象（模板里能用 request.user）
#       auth      注入 user / perms（模板里能用 {% if user.is_authenticated %}）
#       messages  注入 messages（模板里能显示提示消息）
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# =============================================================================
# 5. 应用入口
# =============================================================================
# WSGI：同步标准（gunicorn、uWSGI 用），生产部署的默认方式。
WSGI_APPLICATION = "config.wsgi.application"
# ASGI：异步标准（支持 WebSocket、长连接），本项目暂未使用但保留结构。
ASGI_APPLICATION = "config.asgi.application"

# =============================================================================
# 6. DATABASES：数据库连接（MySQL）
# =============================================================================
# 本项目复用机器上已有的 MySQL Docker 容器，映射到宿主机 3307 端口
# （3306 常被本机原生 MySQL 占用，所以 Docker 里特意映射成 3307）。
#
# 每个字段的含义：
#   ENGINE    Django 的数据库后端。MySQL 固定写 django.db.backends.mysql。
#             注意：底层驱动是 PyMySQL（见 config/__init__.py 的「伪装」），
#             这里不需要（也不能）写 pymysql。
#   NAME      数据库名。要在 MySQL 里先建好（CREATE DATABASE practice_db ...），
#             Django 不会自动帮你建库，只会建表。
#   USER / PASSWORD  登录 MySQL 的账号密码。
#   HOST      数据库 IP。127.0.0.1 表示本机。
#             如果 Django 也跑在 Docker 里，这里要写容器名（如 mysql）。
#   PORT      端口。注意是字符串 "3307"，写整数通常也不报错，
#             但官方文档示例是字符串，保持一致更稳妥。
#   OPTIONS   charset=utf8mb4 才能存 emoji（😀）和生僻字；
#             utf8（=utf8mb3）最多 3 字节，存 emoji 会报
#             "Incorrect string value"。
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DB", "practice_db"),
        "USER": os.getenv("MYSQL_USER", "django"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", "Henhaoji@119"),
        "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "PORT": os.getenv("MYSQL_PORT", "3307"),
        # utf8mb4 才能存中文和 emoji
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# =============================================================================
# 7. CACHES：缓存（Redis）
# =============================================================================
# 我们用它做「列表接口结果缓存」：同样的查询第二次直接返回缓存，
# 不去查数据库，速度从几十毫秒降到 1 毫秒级别。
#
# ★ Redis 有 16 个逻辑库，编号 0~15，彼此隔离（像 16 个独立的 Redis）。
#   本项目约定：
#       0、1 号库   → 另一个项目（project1）在用
#       2 号库      → 本项目缓存  ← 就是下面这个
#       3 号库      → 本项目 Celery（见文件最后）
#   分库的好处：keys 不混在一起，调试时 FLUSHDB 只影响自己那个库。
#
# ★ 密码里的 @ 必须写成 %40：
#   URL 格式是 redis://用户:密码@主机:端口/库号
#   密码 Henhaoji@119 中的 @ 是 URL 分隔符，直接写会把地址解析错，
#   所以要做 URL 编码：@ → %40。
#   其它常见转义：# → %23，/ → %2F，: → %3A。
CACHES = {
    "default": {
        # Django 4.0+ 内置的 Redis 缓存后端（依赖 redis-py 库，不需要 django-redis）
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv(
            "REDIS_CACHE_URL", "redis://:Henhaoji%40119@127.0.0.1:6380/2"
        ),
    }
}

# =============================================================================
# 8. 密码校验器
# =============================================================================
# 只在「创建用户、修改密码」时生效（本项目的图书接口用不到）。
# 四个校验器分别是：
#   UserAttributeSimilarityValidator  密码不能和用户名/邮箱太像
#   MinimumLengthValidator            默认最少 8 位
#   CommonPasswordValidator           不能是 123456 这类常见弱密码
#   NumericPasswordValidator          不能全是数字
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================================
# 9. 国际化与时区
# =============================================================================
# 界面语言（admin 后台会变成中文）
LANGUAGE_CODE = "zh-hans"
# 时区。存进数据库时 Django 会统一存 UTC，显示时再按这个时区转换。
TIME_ZONE = "Asia/Shanghai"
# 启用翻译系统
USE_I18N = True
# 启用「带时区的时间」。
# ★ 开启后 datetime.now() 拿到的是「naive」时间会有警告，
#   应该用 django.utils.timezone.now()（本项目在 models 的 auto_now_add 里由 Django 处理）。
USE_TZ = True

# 静态文件（CSS/JS）的 URL 前缀。开发时 DEBUG=True 由 runserver 直接提供。
STATIC_URL = "static/"

# 模型主键的默认类型。
# 老版本默认 AutoField（int，上限 21 亿）；
# 新版本默认 BigAutoField（bigint，上限 922 亿亿），基本不用担心 id 用光。
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# 10. REST_FRAMEWORK：DRF 的全局默认配置
# =============================================================================
# 这里的配置对所有视图生效，视图里也可以单独覆盖（如分类接口 pagination_class = None）。
REST_FRAMEWORK = {
    # 权限：AllowAny = 匿名也能访问。
    # 学习项目为了用 curl/Postman 直接调不折腾鉴权，所以放开了。
    # 上线一定要改成 IsAuthenticated（必须登录）或更细的自定义权限。
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],

    # 分页器：PageNumberPagination = 按页码分页（?page=2&page_size=...）。
    # 另一种常见的是 LimitOffsetPagination（?limit=10&offset=20）。
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",

    # 每页条数。
    # ★ 前端的「每页 N 条」必须和这里保持一致（practice 前端 pageSize 也是 5），
    #   否则会出现「前端以为 10 条、后端只给 5 条」的诡异现象。
    # ★ 也可以在视图里自定义 pagination_class 来改 page_size，
    #   或者给分页器加 page_size_query_param 让前端用参数控制。
    "PAGE_SIZE": 5,

    # 过滤器后端：
    #   SearchFilter   把 ?search=xxx 翻译成 ORM 的 icontains（不区分大小写模糊匹配）
    #   OrderingFilter 把 ?ordering=-price 翻译成 order_by("-price")（负号=倒序）
    # 视图里还要声明 search_fields / ordering_fields 才知道搜哪些字段、能按哪些字段排。
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# =============================================================================
# 11. CORS：跨域白名单
# =============================================================================
# 什么是跨域？浏览器的同源策略规定：
#   协议 + 域名 + 端口 三者完全相同才算「同源」，否则就是跨域。
#
# 本项目的组合：
#   前端 http://localhost:5174   后端 http://127.0.0.1:8001
#   → 端口不同、域名也不同 → 跨域
#
# 如果不配置这一项，浏览器控制台会报：
#   Access to XMLHttpRequest at 'http://127.0.0.1:8001/api/books/'
#   from origin 'http://localhost:5174' has been blocked by CORS policy
#
# ★ 注意必须把 localhost 和 127.0.0.1 两种写法都写上：
#   浏览器认为它们不是同一个源（虽然指向同一台机器）。
# ★ practice 前端特意用了 5174（另一个项目用 5173），
#   好处是两个项目可以同时启动、互不干扰。
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

# =============================================================================
# 12. Celery：异步任务队列
# =============================================================================
# Celery 由三部分组成：
#   producer  生产者（Django Web 进程），用 task.delay() 把任务丢进队列
#   broker    队列本体，通常是 Redis/RabbitMQ   ← CELERY_BROKER_URL
#   worker    消费者（另一个独立进程，用命令启动），真正干活
#
# 我们这里把 broker 和 backend 都指向 Redis 的 3 号库：
#   broker  存「还没被执行的排队任务」
#   backend 存「任务执行结果和状态」，前端才能轮询 /api/tasks/<id>/ 查询
#
# ★ 两者其实最好分开（broker 用 3 号库、backend 用 4 号库），
#   但学习项目放一个库里也能正常工作，只是 redis-cli 看 keys 时混在一起。
CELERY_BROKER_URL = os.getenv(
    "REDIS_URL", "redis://:Henhaoji%40119@127.0.0.1:6380/3"
)
# 结果后端直接用 broker 的地址（都指向同一个 Redis）
CELERY_RESULT_BACKEND = CELERY_BROKER_URL

# 任务一开始执行就把状态设成 STARTED。
# 默认情况下状态只有 PENDING → SUCCESS，
# 打开了这一项才看得到「正在执行」，前端进度条才能动起来。
CELERY_TASK_TRACK_STARTED = True

# Celery 的时区跟随 Django。
# 不设置的话定时任务（celery beat）的时间会和预期差 8 小时。
CELERY_TIMEZONE = TIME_ZONE
