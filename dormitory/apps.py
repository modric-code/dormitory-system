"""App 配置"""
from django.apps import AppConfig


class DormitoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dormitory'              # App 名称
    verbose_name = '宿舍管理'       # 中文显示名
