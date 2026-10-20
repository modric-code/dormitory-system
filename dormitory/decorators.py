"""权限装饰器：实现管理员 / 学生两种角色的访问控制"""
from functools import wraps
from django.shortcuts import redirect, render


def admin_required(view_func):
    """仅允许管理员访问：未登录跳登录页，非管理员返回 403"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'admin':
            return render(request, 'dormitory/403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """仅允许学生访问"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'student':
            return render(request, 'dormitory/403.html', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper
