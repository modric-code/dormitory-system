"""
Django 项目全局配置文件
包含：数据库、应用注册、模板、语言、静态文件、自定义用户模型等配置
"""
import os
from pathlib import Path

# 项目根目录（manage.py 所在目录）
BASE_DIR = Path(__file__).resolve().parent.parent

# 安全密钥：从环境变量读取，未设置时使用开发用占位密钥（勿用于生产）
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-only-not-for-production')

# 调试模式：开发时开启，部署上线必须关闭
DEBUG = True

# 允许访问的主机（* 表示任意）
ALLOWED_HOSTS = ['*']

# 已安装的应用
INSTALLED_APPS = [
    'django.contrib.admin',          # 后台管理
    'django.contrib.auth',           # 认证系统
    'django.contrib.contenttypes',   # 内容类型
    'django.contrib.sessions',       # 会话
    'django.contrib.messages',       # 消息提示
    'django.contrib.staticfiles',    # 静态文件
    'dormitory',                     # 宿舍管理核心业务应用
]

# 中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',          # CSRF 防护
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 根路由配置
ROOT_URLCONF = 'dormitory_system.urls'

# 模板配置
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],                      # 使用各 app 内部的 templates 目录
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI 入口
WSGI_APPLICATION = 'dormitory_system.wsgi.application'

# 数据库配置：使用 SQLite 文件型数据库，无需安装任何数据库服务
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',   # 数据库引擎：SQLite
        'NAME': BASE_DIR / 'db.sqlite3',          # 数据库文件路径
    }
}

# 密码强度校验规则（已放宽：课程作业方便测试，密码无强度限制，可随意设置）
AUTH_PASSWORD_VALIDATORS = []

# 国际化与本地化
LANGUAGE_CODE = 'zh-hans'          # 界面语言：简体中文
TIME_ZONE = 'Asia/Shanghai'        # 时区：上海
USE_I18N = True
USE_TZ = True

# 静态文件 URL
STATIC_URL = 'static/'

# 默认主键字段类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 自定义用户模型（权限管理的核心）
AUTH_USER_MODEL = 'dormitory.User'

# 登录相关跳转地址
LOGIN_URL = 'login'                # 未登录时跳转的登录页
LOGIN_REDIRECT_URL = 'dashboard'   # 登录成功后跳转页
LOGOUT_REDIRECT_URL = 'login'      # 退出后跳转页
