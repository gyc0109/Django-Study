"""
Django 项目的「总配置文件」。

一个 Django 项目启动时，第一件事就是读取这个文件，
里面写着：用哪个数据库、装了哪些功能、语言时区、Celery 连哪个 Redis 等等。
你可以把它理解成整个后端的「控制面板」。

阅读顺序建议：
1. BASE_DIR / .env        -> 项目根目录和环境变量
2. INSTALLED_APPS         -> 启用了哪些功能模块
3. MIDDLEWARE             -> 请求进来后按顺序经过的「关卡」
4. DATABASES / CACHES     -> MySQL 和 Redis 的连接信息
5. REST_FRAMEWORK         -> 接口的分页、搜索、权限
6. CELERY_*               -> 异步任务队列的配置
"""

import os
from pathlib import Path

# python-dotenv：把 .env 文件里的键值对读进环境变量，
# 这样密码等敏感信息就不会硬编码在代码里，也不会提交到 Git。
from dotenv import load_dotenv

# BASE_DIR = 项目根目录（backend/）。
# __file__ 是当前文件路径；.resolve() 转成绝对路径；
# .parent 是 config/ 目录，再 .parent 就是 backend/ 目录。
BASE_DIR = Path(__file__).resolve().parent.parent

# 读取 backend/.env 文件，把里面的 MYSQL_PASSWORD 等变量加载到 os.environ。
# 如果 .env 不存在也不会报错，后面 os.getenv 会使用默认值。
load_dotenv(BASE_DIR / ".env")

# SECRET_KEY 用于加密签名（session、密码重置链接等）。
# 开发环境可以随便写；上线必须换成随机长字符串并保密。
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-key-change-me")

# DEBUG=1 表示开发模式：报错时显示详细堆栈，方便调试。
# 上线必须改成 0，否则会泄露代码细节。
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

# 允许哪些域名访问后端。["*"] 表示全部允许，仅限本地学习使用。
ALLOWED_HOSTS = ["*"]

# INSTALLED_APPS：Django 启动时加载的功能模块列表。
# 前 6 个是 Django 自带的后台管理、用户、会话等；
# rest_framework 是 DRF，用来写 REST API；
# corsheaders 负责跨域；core 是我们自己写的业务 app。
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

# MIDDLEWARE：中间件。每个 HTTP 请求会从上到下依次经过这些「关卡」，
# 响应回来时再从下到上离开。顺序很重要，不要随意打乱。
MIDDLEWARE = [
    # 跨域中间件要尽量靠前，保证预检请求（OPTIONS）能被正确处理
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",              # 安全相关响应头
    "django.contrib.sessions.middleware.SessionMiddleware",       # 解析 session
    "django.middleware.common.CommonMiddleware",                  # 通用处理（如斜杠补全）
    "django.middleware.csrf.CsrfViewMiddleware",                  # CSRF 防护
    "django.contrib.auth.middleware.AuthenticationMiddleware",    # 把用户挂到 request.user
    "django.contrib.messages.middleware.MessageMiddleware",       # 消息提示
    "django.middleware.clickjacking.XFrameOptionsMiddleware",     # 防点击劫持
]

# 根路由文件：所有 URL 都从这里开始匹配（config/urls.py）。
ROOT_URLCONF = "config.urls"

# 模板引擎配置。本项目主要写 API，几乎用不到 HTML 模板，
# 但 Django 自带后台（admin）需要它，所以保留默认配置。
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

# 项目的 WSGI / ASGI 入口，部署时由 gunicorn / uvicorn 使用。
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# DATABASES：数据库配置。
# 本项目用 Docker 里的 MySQL 8.4，映射到宿主机的 3307 端口，
# 所以 HOST=127.0.0.1、PORT=3307（不是默认的 3306，避免和系统库冲突）。
# 所有值都优先从 .env 读取，读不到才用逗号后的默认值。
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

# CACHES：缓存配置，这里用 Redis。
# 注意 URL 格式：redis://:密码@主机:端口/库编号
# 密码里的 @ 必须转义成 %40，否则解析会错乱（这是个常见坑）。
# 结尾的 /1 表示使用 Redis 的第 1 号库（共 16 个库，0~15）。
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv(
            "REDIS_CACHE_URL", "redis://:Henhaoji%40119@127.0.0.1:6380/1"
        ),
    }
}

# 密码强度校验规则（创建用户、改密码时生效）。
AUTH_PASSWORD_VALIDATORS = [
    # 密码不能和用户名/邮箱太像
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    # 密码长度不能太短（默认 8 位）
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    # 不能是 123456、password 这类常见弱密码
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    # 不能是纯数字
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# 后台和报错信息使用简体中文；时区用上海；USE_TZ 表示数据库存 UTC 时间。
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

# 静态文件（admin 后台的 css/js）的访问前缀。
STATIC_URL = "static/"

# 模型主键默认使用 BigAutoField（64 位自增 ID）。
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST_FRAMEWORK：DRF 的全局配置，对所有接口生效。
REST_FRAMEWORK = {
    # 默认允许任何人访问（学习项目简化处理；上线要改成登录后才能访问）
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    # 分页：默认每页 5 条，前端通过 ?page=2 翻页
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 5,
    # 过滤：SearchFilter 支持 ?search=关键词，OrderingFilter 支持 ?ordering=字段
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# CORS：允许哪些前端地址跨域访问后端。
# 前端跑在 5173 端口，所以把 localhost 和 127.0.0.1 都列上。
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# ---------------- Celery 异步任务配置 ----------------
# broker：任务队列，这里用 Redis 的 0 号库。
# backend：任务结果也存 Redis，前端才能查到任务结果。
# 密码同样需要 %40 转义。
CELERY_BROKER_URL = os.getenv(
    "REDIS_URL", "redis://:Henhaoji%40119@127.0.0.1:6380/0"
)
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
# 任务一开始执行就把状态记为 STARTED，方便前端看到进度
CELERY_TASK_TRACK_STARTED = True
# 任务里的时间使用项目时区
CELERY_TIMEZONE = TIME_ZONE
