"""视图函数：实现登录、学生/楼栋/房间/入住/调宿/维修/统计等全部业务逻辑"""
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse
from django.utils import timezone

from .models import User, Student, Dormitory, Room, CheckIn, TransferRecord, RepairRequest
from .forms import (RegisterForm, StudentForm, DormitoryForm, RoomForm,
                    CheckInForm, TransferForm, RepairForm)
from .decorators import admin_required, student_required


# ==================== 工具函数 ====================
def sync_room_status(room):
    """根据在住人数自动更新房间状态（空闲 / 已满）"""
    occupied = room.checkins.filter(status='在住').count()
    if room.status == '维修中':
        return
    if occupied >= room.bed_count:
        room.status = '已满'
    else:
        room.status = '空闲'
    room.save()


def paginate(request, queryset, per_page=10):
    """通用分页：返回当前页对象（若无排序则默认按 id 倒序，保证分页结果稳定）"""
    if not queryset.query.order_by:
        queryset = queryset.order_by('-id')
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')
    return paginator.get_page(page)


def filter_students(request):
    """学生多条件筛选（列表页与导出共用）"""
    students = Student.objects.all()
    keyword = request.GET.get('keyword', '').strip()
    college = request.GET.get('college', '').strip()
    status = request.GET.get('status', '').strip()
    if keyword:
        students = students.filter(
            Q(student_no__icontains=keyword) | Q(name__icontains=keyword)
            | Q(major__icontains=keyword) | Q(class_name__icontains=keyword)
        )
    if college:
        students = students.filter(college__icontains=college)
    if status:
        students = students.filter(status=status)
    return students, keyword, college, status


def filter_repairs(request):
    """维修工单多条件筛选（管理员看全部，学生看自己的）"""
    repairs = RepairRequest.objects.select_related('room', 'applicant', 'room__dormitory').all()
    if request.user.role == 'student':
        student = getattr(request.user, 'student', None)
        repairs = repairs.filter(applicant=student) if student else repairs.none()
    status = request.GET.get('status', '').strip()
    rtype = request.GET.get('type', '').strip()
    keyword = request.GET.get('keyword', '').strip()
    if status:
        repairs = repairs.filter(status=status)
    if rtype:
        repairs = repairs.filter(repair_type=rtype)
    if keyword:
        repairs = repairs.filter(
            Q(room__room_no__icontains=keyword) | Q(applicant__name__icontains=keyword)
            | Q(description__icontains=keyword)
        )
    return repairs, status, rtype, keyword


# ==================== 登录 / 注册 / 退出 ====================
def user_login(request):
    """用户登录"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        messages.error(request, '用户名或密码错误！')
    return render(request, 'dormitory/login.html')


def register(request):
    """学生自助注册"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '注册成功，请登录！')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'dormitory/register.html', {'form': form})


def user_logout(request):
    """退出登录"""
    auth_logout(request)
    return redirect('login')


# ==================== 首页 / 工作台 ====================
@login_required
def dashboard(request):
    """工作台：管理员看整体概览，学生看个人信息与我的报修"""
    if request.user.role == 'admin':
        total_beds = sum(r.bed_count for r in Room.objects.all())
        occupied = CheckIn.objects.filter(status='在住').count()
        rate = round(occupied / total_beds * 100, 1) if total_beds else 0
        context = {
            'student_count': Student.objects.count(),
            'dormitory_count': Dormitory.objects.count(),
            'room_count': Room.objects.count(),
            'total_beds': total_beds,
            'occupied': occupied,
            'rate': rate,
            'repair_pending': RepairRequest.objects.filter(status='待处理').count(),
            'repair_doing': RepairRequest.objects.filter(status='处理中').count(),
            'recent_repairs': RepairRequest.objects.order_by('-created_at')[:5],
        }
    else:
        student = getattr(request.user, 'student', None)
        checkin = student.checkins.filter(status='在住').first() if student else None
        my_repairs = RepairRequest.objects.filter(applicant=student).order_by('-created_at')[:5] if student else []
        context = {'student': student, 'checkin': checkin, 'my_repairs': my_repairs}
    return render(request, 'dormitory/dashboard.html', context)


# ==================== 学生管理（管理员） ====================
@admin_required
def student_list(request):
    """学生列表 + 多条件查询 + 分页"""
    students, keyword, college, status = filter_students(request)
    page_obj = paginate(request, students)
    return render(request, 'dormitory/student_list.html',
                  {'page_obj': page_obj, 'keyword': keyword, 'college': college, 'status': status})


@admin_required
def student_export(request):
    """导出学生名单为 CSV 文件（Excel 可直接打开）"""
    students, _, _, _ = filter_students(request)
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')  # utf-8-sig 让 Excel 正确识别中文
    response['Content-Disposition'] = 'attachment; filename="学生名单.csv"'
    writer = csv.writer(response)
    writer.writerow(['学号', '姓名', '性别', '学院', '专业', '班级', '联系电话', '住宿状态'])
    for s in students:
        writer.writerow([s.student_no, s.name, s.gender, s.college, s.major,
                         s.class_name, s.phone, s.status])
    return response


@admin_required
def student_add(request):
    """添加学生（可同时创建登录账号）"""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            if username:   # 填写了登录账号则创建用户并关联
                if User.objects.filter(username=username).exists():
                    messages.error(request, '该登录账号已存在！')
                    return render(request, 'dormitory/student_form.html',
                                  {'form': form, 'title': '添加学生', 'show_account': True})
                user = User.objects.create_user(
                    username=username, password=password or '123456',
                    role='student', phone=student.phone
                )
                student.user = user
            student.save()
            messages.success(request, '学生添加成功！')
            return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'dormitory/student_form.html',
                  {'form': form, 'title': '添加学生', 'show_account': True})


@admin_required
def student_edit(request, pk):
    """编辑学生信息"""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, '学生信息修改成功！')
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    return render(request, 'dormitory/student_form.html',
                  {'form': form, 'title': '编辑学生', 'show_account': False})


@admin_required
def student_delete(request, pk):
    """删除学生"""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.delete()
        messages.success(request, '学生删除成功！')
        return redirect('student_list')
    return render(request, 'dormitory/confirm_delete.html',
                  {'obj': student, 'cancel_url': '/students/'})


# ==================== 宿舍楼管理（管理员） ====================
@admin_required
def dormitory_list(request):
    """宿舍楼列表 + 分页"""
    dormitories = Dormitory.objects.all()
    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        dormitories = dormitories.filter(name__icontains=keyword)
    dormitories = dormitories.annotate(room_count=Count('rooms'))
    page_obj = paginate(request, dormitories)
    return render(request, 'dormitory/dormitory_list.html',
                  {'page_obj': page_obj, 'keyword': keyword})


@admin_required
def dormitory_add(request):
    """添加宿舍楼"""
    if request.method == 'POST':
        form = DormitoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '宿舍楼添加成功！')
            return redirect('dormitory_list')
    else:
        form = DormitoryForm()
    return render(request, 'dormitory/dormitory_form.html', {'form': form, 'title': '添加宿舍楼'})


@admin_required
def dormitory_edit(request, pk):
    """编辑宿舍楼"""
    dormitory = get_object_or_404(Dormitory, pk=pk)
    if request.method == 'POST':
        form = DormitoryForm(request.POST, instance=dormitory)
        if form.is_valid():
            form.save()
            messages.success(request, '宿舍楼修改成功！')
            return redirect('dormitory_list')
    else:
        form = DormitoryForm(instance=dormitory)
    return render(request, 'dormitory/dormitory_form.html', {'form': form, 'title': '编辑宿舍楼'})


@admin_required
def dormitory_delete(request, pk):
    """删除宿舍楼（会级联删除其下房间）"""
    dormitory = get_object_or_404(Dormitory, pk=pk)
    if request.method == 'POST':
        dormitory.delete()
        messages.success(request, '宿舍楼删除成功！')
        return redirect('dormitory_list')
    return render(request, 'dormitory/confirm_delete.html',
                  {'obj': dormitory, 'cancel_url': '/dormitories/'})


# ==================== 房间管理（管理员） ====================
@admin_required
def room_list(request):
    """房间列表 + 多条件查询 + 分页"""
    rooms = Room.objects.select_related('dormitory').all()
    dorm_id = request.GET.get('dormitory', '').strip()
    floor = request.GET.get('floor', '').strip()
    status = request.GET.get('status', '').strip()
    keyword = request.GET.get('keyword', '').strip()
    if dorm_id:
        rooms = rooms.filter(dormitory_id=dorm_id)
    if floor:
        rooms = rooms.filter(floor=floor)
    if status:
        rooms = rooms.filter(status=status)
    if keyword:
        rooms = rooms.filter(room_no__icontains=keyword)
    page_obj = paginate(request, rooms)
    return render(request, 'dormitory/room_list.html', {
        'page_obj': page_obj, 'dormitories': Dormitory.objects.all(),
        'dorm_id': dorm_id, 'floor': floor, 'status': status, 'keyword': keyword,
    })


@admin_required
def room_add(request):
    """添加房间"""
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '房间添加成功！')
            return redirect('room_list')
    else:
        form = RoomForm()
    return render(request, 'dormitory/room_form.html', {'form': form, 'title': '添加房间'})


@admin_required
def room_edit(request, pk):
    """编辑房间"""
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            sync_room_status(room)
            messages.success(request, '房间修改成功！')
            return redirect('room_list')
    else:
        form = RoomForm(instance=room)
    return render(request, 'dormitory/room_form.html', {'form': form, 'title': '编辑房间'})


@admin_required
def room_delete(request, pk):
    """删除房间"""
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'POST':
        room.delete()
        messages.success(request, '房间删除成功！')
        return redirect('room_list')
    return render(request, 'dormitory/confirm_delete.html',
                  {'obj': room, 'cancel_url': '/rooms/'})


# ==================== 入住管理（管理员） ====================
@admin_required
def checkin_list(request):
    """入住记录列表 + 多条件查询 + 分页"""
    checkins = CheckIn.objects.select_related('student', 'room', 'room__dormitory').all()
    status = request.GET.get('status', '').strip()
    keyword = request.GET.get('keyword', '').strip()
    if status:
        checkins = checkins.filter(status=status)
    if keyword:
        checkins = checkins.filter(
            Q(student__name__icontains=keyword) | Q(student__student_no__icontains=keyword)
            | Q(room__room_no__icontains=keyword)
        )
    page_obj = paginate(request, checkins)
    return render(request, 'dormitory/checkin_list.html',
                  {'page_obj': page_obj, 'status': status, 'keyword': keyword})


@admin_required
def checkin_add(request):
    """办理入住（宿舍分配）"""
    if request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            room = form.cleaned_data['room']
            # 业务校验：学生是否已有在住 / 房间是否维修 / 是否满员
            if student.checkins.filter(status='在住').exists():
                messages.error(request, '该学生已有在住的宿舍记录，请先办理退宿！')
            elif room.status == '维修中':
                messages.error(request, '该房间维修中，暂无法入住！')
            elif room.checkins.filter(status='在住').count() >= room.bed_count:
                messages.error(request, '该房间已满，无法入住！')
            else:
                checkin = form.save(commit=False)
                checkin.status = '在住'
                checkin.save()
                student.status = '在住'
                student.save()
                sync_room_status(room)
                messages.success(request, '入住办理成功！')
                return redirect('checkin_list')
    else:
        form = CheckInForm()
    return render(request, 'dormitory/checkin_form.html', {'form': form, 'title': '办理入住'})


@admin_required
def checkin_checkout(request, pk):
    """办理退宿"""
    checkin = get_object_or_404(CheckIn, pk=pk)
    if checkin.status == '在住':
        checkin.status = '已退宿'
        checkin.checkout_date = timezone.now().date()
        checkin.save()
        # 若该学生无其它在住记录，则更新学生状态
        if not checkin.student.checkins.filter(status='在住').exists():
            checkin.student.status = '未入住'
            checkin.student.save()
        sync_room_status(checkin.room)
        messages.success(request, '退宿办理成功！')
    return redirect('checkin_list')


@admin_required
def checkin_delete(request, pk):
    """删除入住记录"""
    checkin = get_object_or_404(CheckIn, pk=pk)
    if request.method == 'POST':
        room = checkin.room
        student = checkin.student
        checkin.delete()
        if not student.checkins.filter(status='在住').exists():
            student.status = '未入住'
            student.save()
        sync_room_status(room)
        messages.success(request, '入住记录删除成功！')
        return redirect('checkin_list')
    return render(request, 'dormitory/confirm_delete.html',
                  {'obj': checkin, 'cancel_url': '/checkins/'})


# ==================== 调宿管理（管理员） ====================
@admin_required
def transfer_list(request):
    """调宿记录列表 + 分页"""
    transfers = TransferRecord.objects.select_related('student', 'from_room', 'to_room').all()
    keyword = request.GET.get('keyword', '').strip()
    if keyword:
        transfers = transfers.filter(
            Q(student__name__icontains=keyword) | Q(student__student_no__icontains=keyword)
        )
    page_obj = paginate(request, transfers)
    return render(request, 'dormitory/transfer_list.html',
                  {'page_obj': page_obj, 'keyword': keyword})


@admin_required
def transfer_add(request):
    """办理调宿"""
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            to_room = form.cleaned_data['to_room']
            current = student.checkins.filter(status='在住').first()
            if current is None:
                messages.error(request, '该学生当前没有在住记录，无法调宿！')
            elif current.room == to_room:
                messages.error(request, '目标房间与当前房间相同，无需调宿！')
            elif to_room.status == '维修中':
                messages.error(request, '目标房间维修中，无法调入！')
            elif to_room.checkins.filter(status='在住').count() >= to_room.bed_count:
                messages.error(request, '目标房间已满，无法调入！')
            else:
                transfer = form.save(commit=False)
                transfer.from_room = current.room
                transfer.operator = request.user.username
                transfer.save()
                current.room = to_room      # 更新入住记录到新房间
                current.save()
                sync_room_status(transfer.from_room)
                sync_room_status(to_room)
                messages.success(request, '调宿办理成功！')
                return redirect('transfer_list')
    else:
        form = TransferForm()
    return render(request, 'dormitory/transfer_form.html', {'form': form, 'title': '办理调宿'})


@admin_required
def transfer_delete(request, pk):
    """删除调宿记录"""
    transfer = get_object_or_404(TransferRecord, pk=pk)
    if request.method == 'POST':
        transfer.delete()
        messages.success(request, '调宿记录删除成功！')
        return redirect('transfer_list')
    return render(request, 'dormitory/confirm_delete.html',
                  {'obj': transfer, 'cancel_url': '/transfers/'})


# ==================== 维修管理 ====================
@login_required
def repair_list(request):
    """维修工单列表 + 多条件查询 + 分页"""
    repairs, status, rtype, keyword = filter_repairs(request)
    page_obj = paginate(request, repairs)
    return render(request, 'dormitory/repair_list.html',
                  {'page_obj': page_obj, 'status': status, 'rtype': rtype, 'keyword': keyword})


@login_required
def repair_export(request):
    """导出维修工单为 CSV 文件（Excel 可直接打开）"""
    repairs, _, _, _ = filter_repairs(request)
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="维修工单.csv"'
    writer = csv.writer(response)
    writer.writerow(['工单号', '楼栋', '房间号', '申请人', '类型', '状态', '报修日期', '问题描述', '处理人', '完成日期'])
    for r in repairs:
        writer.writerow([r.order_no, r.room.dormitory.name, r.room.room_no,
                         r.applicant.name, r.repair_type, r.status, r.apply_date,
                         r.description, r.handler, r.finish_date or ''])
    return response


@login_required
def repair_add(request):
    """提交报修申请（学生自动带入自己与房间；管理员可代报）"""
    if request.method == 'POST':
        form = RepairForm(request.POST)
        if form.is_valid():
            repair = form.save(commit=False)
            if request.user.role == 'student':
                student = getattr(request.user, 'student', None)
                if student is None:
                    messages.error(request, '未找到您的学生信息，请联系管理员！')
                    return redirect('repair_add')
                repair.applicant = student
                current = student.checkins.filter(status='在住').first()
                if current:
                    repair.room = current.room   # 自动使用当前入住房间
                repair.save()
                messages.success(request, '报修申请提交成功！')
                return redirect('repair_list')
            else:
                # 管理员代报：需指定申请人
                applicant_id = request.POST.get('applicant', '').strip()
                if applicant_id:
                    repair.applicant = get_object_or_404(Student, pk=applicant_id)
                repair.save()
                messages.success(request, '报修工单创建成功！')
                return redirect('repair_list')
    else:
        form = RepairForm()
    return render(request, 'dormitory/repair_form.html',
                  {'form': form, 'students': Student.objects.all()})


@login_required
def repair_detail(request, pk):
    """工单详情 + 进度处理（管理员可更新状态/进度）"""
    repair = get_object_or_404(RepairRequest.objects.select_related('room', 'applicant'), pk=pk)
    # 权限：学生只能看自己的工单
    if request.user.role == 'student':
        student = getattr(request.user, 'student', None)
        if not student or repair.applicant_id != student.id:
            return render(request, 'dormitory/403.html', status=403)
    if request.method == 'POST' and request.user.role == 'admin':
        repair.status = request.POST.get('status', repair.status)
        repair.handler = request.POST.get('handler', '').strip()
        repair.progress = request.POST.get('progress', '').strip()
        if repair.status == '已完成':
            repair.finish_date = timezone.now().date()
        else:
            repair.finish_date = None
        repair.save()
        messages.success(request, '工单更新成功！')
        return redirect('repair_detail', pk=repair.pk)
    return render(request, 'dormitory/repair_detail.html', {'repair': repair})


@admin_required
def repair_delete(request, pk):
    """删除工单"""
    repair = get_object_or_404(RepairRequest, pk=pk)
    if request.method == 'POST':
        repair.delete()
        messages.success(request, '工单删除成功！')
        return redirect('repair_list')
    return render(request, 'dormitory/confirm_delete.html',
                  {'obj': repair, 'cancel_url': '/repairs/'})


# ==================== 学生端：我的宿舍 ====================
@student_required
def my_room(request):
    """学生查看自己的宿舍信息"""
    student = getattr(request.user, 'student', None)
    checkin = student.checkins.filter(status='在住').first() if student else None
    return render(request, 'dormitory/my_room.html', {'student': student, 'checkin': checkin})


# ==================== 数据统计（管理员） ====================
@admin_required
def statistics(request):
    """宿舍入住率统计 + 维修工单统计"""
    dorm_stats = []
    total_beds = 0
    total_occupied = 0
    for d in Dormitory.objects.all():
        beds = sum(r.bed_count for r in d.rooms.all())
        occupied = CheckIn.objects.filter(status='在住', room__dormitory=d).count()
        total_beds += beds
        total_occupied += occupied
        rate = round(occupied / beds * 100, 1) if beds else 0
        dorm_stats.append({'name': d.name, 'beds': beds, 'occupied': occupied, 'rate': rate})
    overall_rate = round(total_occupied / total_beds * 100, 1) if total_beds else 0

    repair_by_status = RepairRequest.objects.values('status').annotate(count=Count('id')).order_by()
    repair_by_type = RepairRequest.objects.values('repair_type').annotate(count=Count('id')).order_by()

    return render(request, 'dormitory/statistics.html', {
        'dorm_stats': dorm_stats, 'total_beds': total_beds, 'total_occupied': total_occupied,
        'overall_rate': overall_rate,
        'repair_by_status': repair_by_status, 'repair_by_type': repair_by_type,
        'student_total': Student.objects.count(),
        'student_in': Student.objects.filter(status='在住').count(),
        'repair_total': RepairRequest.objects.count(),
    })
