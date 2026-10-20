"""后台管理注册：方便在 /admin 中直接管理数据"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Student, Dormitory, Room, CheckIn, TransferRecord, RepairRequest


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'role', 'phone', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff']
    # 在编辑页增加角色/电话字段
    fieldsets = UserAdmin.fieldsets + (('角色信息', {'fields': ('role', 'phone')}),)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_no', 'name', 'gender', 'college', 'major', 'class_name', 'status']
    search_fields = ['student_no', 'name']
    list_filter = ['status', 'gender']


@admin.register(Dormitory)
class DormitoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'floors', 'gender', 'manager']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['dormitory', 'room_no', 'floor', 'bed_count', 'gender', 'status']
    list_filter = ['dormitory', 'status']


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ['student', 'room', 'bed_no', 'checkin_date', 'status']


@admin.register(TransferRecord)
class TransferRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'from_room', 'to_room', 'transfer_date', 'operator']


@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'room', 'applicant', 'repair_type', 'status', 'apply_date']
    list_filter = ['status', 'repair_type']
