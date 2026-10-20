"""项目根路由：把请求分发到后台管理与本系统 App"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),        # Django 自带后台管理
    path('', include('dormitory.urls')),    # 宿舍管理系统业务路由
]
