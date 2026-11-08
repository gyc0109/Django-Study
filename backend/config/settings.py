"""
project1 的「总配置文件」（settings.py）。

===============================================================================
一、这个文件是什么？
===============================================================================
Django 项目启动时，第一件事就是执行这个文件。它决定了：
    - 用哪个数据库、缓存、消息队列
    - 装了哪些功能模块（app）
    - 每个请求要经过哪些中间件
    - 接口默认的分页、搜索、权限策略
    - 允许哪个前端地址跨域访问

可以把它理解成整个后端的「控制面板」。改错一行，项目可能直接起不来。

===============================================================================
二、阅读顺序（和真实开发时的思考顺序一致）
===============================================================================
    1. BASE_DIR / .env       项目根目录在哪、敏感配置从哪来
    2. INSTALLED_APPS        启用了哪些功能模块
    3. MIDDLEWARE            请求进来后按顺序经过的「关卡」
    4. DATABASES / CACHES    MySQL 和 Redis 的连接信息
    5. REST_FRAMEWORK        接口的分页、搜索、权限
    6. CORS_ALLOWED_ORIGINS  允许哪个前端地址跨域
    7. CELERY_*              异步任务队列连哪个 Redis 库

===============================================================================
三、为什么密码要用 os.getenv 而不是直接写死？
===============================================================================
因为代码要上传到 GitHub。密码写死在代码里 = 公网可查。
标准做法：
    代码  →  os.getenv("MYSQL_PASSWORD", "本地默认值")
    真值  →  放在 backend/.env（已被 .gitignore 忽略）
这样本地能跑、仓库不泄露、服务器部署时改环境变量即可。
"""

# =============================================================================
# 0. 导入
# =============================================================================
# os：读环境变量（os.getenv）和设置环境变量
import os
# Path：面向对象的路径操作，避免手写字符串拼接
from pathlib import Path

# python-dotenv：把 .env 文件的键值对读进环境变量，
# 这样密码等敏感信息就不会硬编码在代码里，也不会提交到 Git。
from dotenv import load_dotenv

# =============================================================================
# 1. 基础路径与敏感配置
# =============================================================================
# BASE_DIR = 项目根目录（backend/）。
#   __file__            当前文件 = .../backend/config/settings.py
#   .resolve()          转绝对路径
#   .parent             上一级 = .../backend/config/
#   .parent.parent      再上一级 = .../backend/     ← 就是这里
BASE_DIR = Path(__file__).resolve().parent.parent

# 读取 backend/.env 文件，把里面的 MYSQL_PASSWORD 等变量加载到 os.environ。
# 如果 .env 不存在也不会报错（load_dotenv 会静默跳过），
# 后面 os.getenv 会使用默认值 —— 所以没建 .env 也能跑起来。
load_dotenv(BASE_DIR / ".env")

# SECRET_KEY 用于加密签名（session、密码重置链接、CSRF token 等）。
# 开发环境可以随便写；上线必须换成随机长字符串并严格保密，
# 一旦泄露，别人可以伪造登录态。
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-key-change-me")

# DEBUG=1 表示开发模式：报错时显示详细堆栈，方便调试，还自动提供静态文件服务。
# 上线必须改成 0，否则会把代码路径、配置、SQL 等细节泄露给用户。
# ★ 注意 os.getenv 读回来是字符串，所以要跟 "1" 比较，不能写 == 1。
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

# 允许哪些域名访问后端。
# ALLOWED_HOSTS 是防「域名劫持」用的：只接受 Host 头在列表里的请求。
# ["*"] 表示全部允许，仅限本地学习使用；上线要写真实域名。
ALLOWED_HOSTS = ["*"]

# =============================================================================
# 2. INSTALLED_APPS：启用了哪些功能模块
# =============================================================================
# 每装一个 app，Django 才会加载它的 models / migrations / templates /
# management commands。前 6 个是 Django 自带的基础功能：
#   admin          自带后台管理页面 /admin/
#   auth           用户与登录认证
#   contenttypes   内容类型框架（auth 依赖它）
#   sessions       会话（默认把 session 存在数据库里）
#   messages       一次性提示消息（如「保存成功」）
#   staticfiles    静态文件（css/js/图片）
# 后 3 个是本项目额外安装的：
#   rest_framework DRF，写 REST API
#   corsheaders    跨域请求支持
#   core           我们自己的业务代码（Note、接口、任务）
INSTALLED_APPS = [
    "django.contrib.admin",          # 自带后台管理页面 /admin/
    "django.contrib.auth",           # 用户与登录认证
    "django.contrib.contenttypes",   # 内容类型框架（auth 依赖它）
    "django.contrib.sessions",       # 会话（默认用数据库存 session）
    "django.contrib.messages",       # 一次性提示消息
    "django.contrib.staticfiles",    # 静态文件（css/js/图片）
    "rest_framework",                # Django REST Framework
    "corsheaders",                   # 跨域请求支持
    "core",                          # 我们的业务代码（Note、接口、任务）
]

# =============================================================================
# 3. MIDDLEWARE：中间件（请求的「关卡」）
# =============================================================================
# 请求流向：浏览器 → 中间件1 → 中间件2 → ... → 视图 → ... → 中间件2 → 中间件1
# 也就是「进去从上到下，出来从下到上」，像洋葱一层层包裹。
# 顺序不能随意打乱，下面逐个说明。
MIDDLEWARE = [
    # 跨域中间件要尽量靠前，保证浏览器的 OPTIONS 预检请求能被及时处理。
    # （预检请求如果先被后面的中间件拒了，跨域就永远通不过。）
    "corsheaders.middleware.CorsMiddleware",
    # 安全相关响应头：HTTPS 重定向、HSTS、X-Content-Type-Options 等
    "django.middleware.security.SecurityMiddleware",
    # 解析 cookie 里的 sessionid，把 session 数据挂到 request.session
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 通用处理：APPEND_SLASH（自动补结尾斜杠）、ETag 等。
    # ★ 坑：APPEND_SLASH 对 GET 是 301 重定向（浏览器自动跟随），
    #   对 POST/PUT/DELETE 直接返回 500。所以调接口时路径结尾的 "/" 必须带上。
    "django.middleware.common.CommonMiddleware",
    # CSRF 防护：防止其它网站冒用你的登录态提交表单。
    # DRF 的接口默认不校验（通常用 token 而非 cookie），主要保护 admin 表单。
    "django.middleware.csrf.CsrfViewMiddleware",
    # 认证：确定 request.user 是谁（匿名用户会是 AnonymousUser）
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # 消息提示：让「保存成功」这类一次性消息能跨请求显示
    "django.contrib.messages.middleware.MessageMiddleware",
    # 防止页面被别的网站用 iframe 嵌套（点击劫持攻击）
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# 根路由文件：所有 URL 都从这里开始匹配（config/urls.py）。
# ★ 必须写「包名.模块名」，因为 config 是一个包，不能只写 "urls"。
ROOT_URLCONF = "config.urls"

# =============================================================================
# 4. TEMPLATES：模板引擎
# =============================================================================
# 本项目主要写 JSON 接口，几乎用不到 HTML 模板，
# 但 Django 自带后台（admin）的页面是用模板渲染的，所以这段不能删。
#
#   BACKEND    用哪个模板引擎（Django 自带的 DTL）
#   DIRS       项目级额外模板目录（空表示不用）
#   APP_DIRS   True = 自动到每个 app 的 templates/ 目录找模板
#   context_processors  自动注入到每个模板上下文里的变量：
#       debug    注入 debug、sql_queries
#       request  注入 request（模板里能用 request.user）
#       auth     注入 user、perms（模板里能用 user.is_authenticated）
#       messages 注入 messages（模板里能显示提示消息）
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],           # 额外的模板目录（空表示不用）
        "APP_DIRS": True,     # 自动到每个 app 的 templates/ 目录找模板
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
# WSGI：同步部署标准，gunicorn / uWSGI 会用（本地 runserver 不走这里）
WSGI_APPLICATION = "config.wsgi.application"
# ASGI：异步部署标准（支持 WebSocket），本项目未使用但保留标准结构
ASGI_APPLICATION = "config.asgi.application"

# =============================================================================
# 6. DATABASES：MySQL 连接
# =============================================================================
# 本项目用 Docker 里的 MySQL 8.4，映射到宿主机的 3307 端口：
#   容器内 3306 → 宿主机 3307
# 之所以不用 3306，是为了避免和宿主机上可能已经安装的 MySQL 冲突。
#
# 字段说明：
#   ENGINE   固定 django.db.backends.mysql（底层驱动是 PyMySQL，见 config/__init__.py）
#   NAME     数据库名。必须先在 MySQL 里 CREATE DATABASE，Django 只建表不建库
#   PORT     字符串 "3307"（官方示例就是字符串，写整数通常也能跑）
#   OPTIONS  charset=utf8mb4：能存中文和 emoji；utf8/utf8mb3 存 emoji 会报错
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",                  # 使用 MySQL 后端
        "NAME": os.getenv("MYSQL_DB", "django_study"),         # 数据库名
        "USER": os.getenv("MYSQL_USER", "django"),             # 用户名
        "PASSWORD": os.getenv("MYSQL_PASSWORD", "Henhaoji@119"),
        "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "PORT": os.getenv("MYSQL_PORT", "3307"),
        # utf8mb4 才能正常存中文和 emoji
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# =============================================================================
# 7. CACHES：Redis 缓存
# =============================================================================
# URL 格式：redis://[:密码@]主机:端口/库编号
#   本例 redis://:Henhaoji%40119@127.0.0.1:6380/1
#     - 用户名部分为空（Redis 6+ 支持 ACL，这里只用了密码）
#     - 端口 6380：Docker 映射到宿主机的端口（容器内是 6379）
#     - 结尾 /1  ：使用第 1 号逻辑库
#
# ★ Redis 默认有 16 个逻辑库（0~15），彼此隔离，像 16 个独立的 Redis。
#   本仓库两个项目的约定：
#       project1（本项目）：0 号 = Celery，1 号 = 缓存  ← 就是这个
#       practice         ：2 号 = 缓存，3 号 = Celery
#   分开的好处是 keys 不会混，调试时 FLUSHDB 不会误删别的项目的数据。
#
# ★ 密码里的 @ 必须转义成 %40！
#   Henhaoji@119 中的 @ 是 URL 里的分隔符（用户:密码@主机），
#   直接写会导致地址解析错乱。其它常见转义：# → %23，/ → %2F，: → %3A。
CACHES = {
    "default": {
        # Django 4.0+ 自带的 Redis 缓存后端，只需要 redis-py，不用装 django-redis
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv(
            "REDIS_CACHE_URL", "redis://:Henhaoji%40119@127.0.0.1:6380/1"
        ),
    }
}

# =============================================================================
# 8. 密码强度校验（创建用户、改密码时生效）
# =============================================================================
AUTH_PASSWORD_VALIDATORS = [
    # 密码不能和用户名/邮箱太像
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    # 密码长度不能太短（默认最少 8 位）
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    # 不能是 123456、password 这类常见弱密码
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    # 不能是纯数字
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# =============================================================================
# 9. 国际化与时区
# =============================================================================
# 后台和报错信息使用简体中文
LANGUAGE_CODE = "zh-hans"
# 时区：上海
TIME_ZONE = "Asia/Shanghai"
# 启用翻译系统
USE_I18N = True
# 数据库统一存 UTC 时间，显示时按 TIME_ZONE 转换。
# 开启后应使用 django.utils.timezone.now() 而不是 datetime.now()。
USE_TZ = True

# 静态文件（admin 后台的 css/js）的访问前缀。
# DEBUG=True 时 runserver 会自动提供这些文件，不需要 collectstatic。
STATIC_URL = "static/"

# 模型主键默认使用 BigAutoField（64 位自增 ID），
# 比老版本的 AutoField（int，上限 21 亿）安全得多。
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# 10. REST_FRAMEWORK：DRF 全局配置（对所有接口生效）
# =============================================================================
REST_FRAMEWORK = {
    # 默认权限：AllowAny = 匿名也能访问。
    # 学习项目为了 curl/Postman 直接调不折腾鉴权；上线要改成 IsAuthenticated。
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],

    # 分页器：按页码分页，前端用 ?page=2 翻页。
    # 返回结构为 { count, next, previous, results }。
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",

    # 每页 5 条。
    # ★ 前端的 pageSize 必须和这里一致，否则总页数会算错。
    "PAGE_SIZE": 5,

    # 过滤器后端：
    #   SearchFilter    ?search=关键词 → 对 search_fields 做 icontains 模糊匹配
    #   OrderingFilter  ?ordering=-id  → 等价于 order_by("-id")
    # 视图里还要声明 search_fields / ordering_fields 才知道搜哪些、排哪些。
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# =============================================================================
# 11. CORS：跨域白名单
# =============================================================================
# 浏览器的同源策略：协议 + 域名 + 端口 三者完全相同才算同源，否则跨域。
#   前端 http://localhost:5173  vs  后端 http://127.0.0.1:8000 → 跨域
# 不配这一段，浏览器控制台会报 "blocked by CORS policy"。
#
# ★ localhost 和 127.0.0.1 要都写上：浏览器认为它们是不同的源。
# ★ 本项目前端固定 5173（practice 项目用的是 5174），两个项目可同时运行。
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# =============================================================================
# 12. Celery 异步任务配置
# =============================================================================
# Celery 三件套：
#   producer（Django）→ broker（Redis 队列）→ worker（执行任务）
#   执行结果存回 result backend（也是 Redis），前端才能查询进度。
#
# 这里 broker 用 0 号库、backend 也用同一个地址（学习项目从简）。
# 密码同样要 %40 转义。
CELERY_BROKER_URL = os.getenv(
    "REDIS_URL", "redis://:Henhaoji%40119@127.0.0.1:6380/0"
)
# 结果后端 = broker 地址（同一个 Redis 的 0 号库）
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
# 任务一开始执行就把状态记为 STARTED，前端才能看到「执行中」，
# 否则状态会从 PENDING 直接跳到 SUCCESS。
CELERY_TASK_TRACK_STARTED = True
# 任务里的时间使用项目时区（否则定时任务会差 8 小时）
CELERY_TIMEZONE = TIME_ZONE
