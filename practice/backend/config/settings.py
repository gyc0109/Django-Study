"""
练习项目「图书管理」的全局配置文件。

阅读顺序（和真实开发时的思考顺序一致）：
    1. BASE_DIR / .env          项目根目录、敏感配置从哪来
    2. INSTALLED_APPS           启用了哪些功能模块
    3. MIDDLEWARE               请求要经过哪些关卡
    4. DATABASES / CACHES       数据存哪里（MySQL / Redis）
    5. REST_FRAMEWORK           接口的分页、搜索、权限
    6. CORS_ALLOWED_ORIGINS     允许哪个前端地址跨域访问
    7. CELERY_*                 异步任务队列怎么连 Redis
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ 目录的绝对路径
BASE_DIR = Path(__file__).resolve().parent.parent

# 读取 backend/.env；文件不存在也不会报错
load_dotenv(BASE_DIR / ".env")

# 加密签名用的密钥。开发环境随便写，上线必须换成随机长字符串
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "practice-insecure-key-change-me")

# 1 = 开发模式（显示详细报错）；上线要改成 0
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"

# 允许哪些域名访问。["*"] 表示不限制，仅限本地学习
ALLOWED_HOSTS = ["*"]

# 启用的功能模块。最后三个是本项目额外安装的：
#   rest_framework -> 写 REST API
#   corsheaders     -> 处理跨域
#   library         -> 自己的业务代码
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

# 中间件：请求从上往下经过，响应从下往上返回
MIDDLEWARE = [
    # 跨域中间件要尽量靠前，才能及时处理浏览器的 OPTIONS 预检请求
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# admin 后台需要模板引擎，保留 Django 默认配置即可
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# MySQL：复用已有 Docker 容器（宿主机 3307），只换数据库名 practice_db
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

# Redis 缓存：使用 2 号库（0/1 已被另一个项目占用，3 号库给 Celery）
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv(
            "REDIS_CACHE_URL", "redis://:Henhaoji%40119@127.0.0.1:6380/2"
        ),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF 全局配置
REST_FRAMEWORK = {
    # 学习项目先允许匿名访问；上线要改成 IsAuthenticated
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    # 分页：每页 5 条，前端通过 ?page=2 翻页
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 5,
    # ?search=关键词 搜索；?ordering=字段 排序
    "DEFAULT_FILTER_BACKENDS": [
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
}

# 前端跑在 5174 端口（本练习项目专门换了一个端口，避免和上一个项目冲突）
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

# ---------------- Celery ----------------
# broker：任务队列（Redis 3 号库）
# backend：任务结果也存 Redis，前端才能轮询到结果
CELERY_BROKER_URL = os.getenv(
    "REDIS_URL", "redis://:Henhaoji%40119@127.0.0.1:6380/3"
)
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
# 任务开始执行就把状态标记为 STARTED，前端能看到进度变化
CELERY_TASK_TRACK_STARTED = True
CELERY_TIMEZONE = TIME_ZONE
