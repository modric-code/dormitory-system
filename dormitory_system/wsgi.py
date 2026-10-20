"""WSGI 配置：用于部署上线（开发时用 runserver 即可）"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dormitory_system.settings')
application = get_wsgi_application()
