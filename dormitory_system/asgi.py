"""ASGI 配置：用于异步部署"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dormitory_system.settings')
application = get_asgi_application()
