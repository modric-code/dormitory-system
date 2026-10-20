"""App 路由：将 URL 映射到对应的视图函数"""
from django.urls import path
from . import views

urlpatterns = [
    # 登录 / 注册 / 退出 / 首页
    path('', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    # 学生管理
    path('students/', views.student_list, name='student_list'),
    path('students/export/', views.student_export, name='student_export'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/edit/<int:pk>/', views.student_edit, name='student_edit'),
    path('students/delete/<int:pk>/', views.student_delete, name='student_delete'),

    # 宿舍楼管理
    path('dormitories/', views.dormitory_list, name='dormitory_list'),
    path('dormitories/add/', views.dormitory_add, name='dormitory_add'),
    path('dormitories/edit/<int:pk>/', views.dormitory_edit, name='dormitory_edit'),
    path('dormitories/delete/<int:pk>/', views.dormitory_delete, name='dormitory_delete'),

    # 房间管理
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/add/', views.room_add, name='room_add'),
    path('rooms/edit/<int:pk>/', views.room_edit, name='room_edit'),
    path('rooms/delete/<int:pk>/', views.room_delete, name='room_delete'),

    # 入住管理
    path('checkins/', views.checkin_list, name='checkin_list'),
    path('checkins/add/', views.checkin_add, name='checkin_add'),
    path('checkins/<int:pk>/checkout/', views.checkin_checkout, name='checkin_checkout'),
    path('checkins/delete/<int:pk>/', views.checkin_delete, name='checkin_delete'),

    # 调宿管理
    path('transfers/', views.transfer_list, name='transfer_list'),
    path('transfers/add/', views.transfer_add, name='transfer_add'),
    path('transfers/delete/<int:pk>/', views.transfer_delete, name='transfer_delete'),

    # 维修管理
    path('repairs/', views.repair_list, name='repair_list'),
    path('repairs/export/', views.repair_export, name='repair_export'),
    path('repairs/add/', views.repair_add, name='repair_add'),
    path('repairs/<int:pk>/', views.repair_detail, name='repair_detail'),
    path('repairs/delete/<int:pk>/', views.repair_delete, name='repair_delete'),

    # 学生端
    path('my_room/', views.my_room, name='my_room'),

    # 数据统计
    path('statistics/', views.statistics, name='statistics'),
]
