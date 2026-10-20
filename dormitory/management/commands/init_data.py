"""初始化演示数据命令：python manage.py init_data
自动创建管理员、测试学生、宿舍楼、房间、入住与维修工单，方便立即演示。"""
from django.core.management.base import BaseCommand
from django.db import transaction
from dormitory.models import User, Student, Dormitory, Room, CheckIn, RepairRequest


class Command(BaseCommand):
    help = '初始化演示数据（管理员、学生、宿舍楼、房间、入住、维修工单）'

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. 管理员账号
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@dorm.com', 'admin123', role='admin')
            self.stdout.write(self.style.SUCCESS('已创建管理员：admin / admin123'))
        else:
            self.stdout.write('管理员已存在，跳过')

        # 2. 测试学生（含登录账号）
        def make_student(username, password, no, name, gender, college, major, cls):
            user, _ = User.objects.get_or_create(username=username,
                                                 defaults={'role': 'student'})
            user.set_password(password)
            user.role = 'student'
            user.save()
            student, _ = Student.objects.get_or_create(
                student_no=no,
                defaults={'user': user, 'name': name, 'gender': gender,
                          'college': college, 'major': major, 'class_name': cls}
            )
            return student

        s1 = make_student('student1', 'student123', '20240001', '张三', '男', '计算机学院', '软件工程', '软工2401')
        s2 = make_student('student2', 'student123', '20240002', '李四', '女', '外国语学院', '英语', '英语2401')
        s3 = make_student('student3', 'student123', '20240003', '王五', '男', '计算机学院', '网络工程', '网工2402')
        self.stdout.write(self.style.SUCCESS('已创建学生账号：student1 / student2 / student3（密码 student123）'))

        # 3. 宿舍楼
        d1, _ = Dormitory.objects.get_or_create(
            name='1号宿舍楼', defaults={'floors': 6, 'gender': '男', 'manager': '赵阿姨'})
        d2, _ = Dormitory.objects.get_or_create(
            name='2号宿舍楼', defaults={'floors': 6, 'gender': '女', 'manager': '钱阿姨'})

        # 4. 房间
        rooms1 = []
        for i in range(1, 4):   # 1号楼 101~103
            r, _ = Room.objects.get_or_create(dormitory=d1, room_no=f'10{i}',
                                              defaults={'floor': 1, 'bed_count': 4, 'gender': '男'})
            rooms1.append(r)
        rooms2 = []
        for i in range(1, 4):   # 2号楼 101~103
            r, _ = Room.objects.get_or_create(dormitory=d2, room_no=f'10{i}',
                                              defaults={'floor': 1, 'bed_count': 4, 'gender': '女'})
            rooms2.append(r)
        self.stdout.write(self.style.SUCCESS('已创建宿舍楼与房间'))

        # 5. 入住记录（张三→1-101，李四→2-101，王五→1-101）
        def checkin(student, room, bed):
            if not student.checkins.filter(status='在住').exists():
                CheckIn.objects.create(student=student, room=room, bed_no=bed, status='在住')
                student.status = '在住'
                student.save()

        checkin(s1, rooms1[0], '1床')
        checkin(s2, rooms2[0], '1床')
        checkin(s3, rooms1[0], '2床')
        # 同步房间状态
        for r in rooms1 + rooms2:
            occupied = r.checkins.filter(status='在住').count()
            r.status = '已满' if occupied >= r.bed_count else '空闲'
            r.save()

        # 6. 维修工单
        if not RepairRequest.objects.exists():
            RepairRequest.objects.create(
                room=rooms1[0], applicant=s1, repair_type='水电',
                description='宿舍灯管损坏，无法照明', status='处理中',
                handler='admin', progress='已上报维修师傅，预计本周处理')
            RepairRequest.objects.create(
                room=rooms2[1], applicant=s2, repair_type='家具',
                description='衣柜门松动，需要加固', status='待处理')
            RepairRequest.objects.create(
                room=rooms1[1], applicant=s3, repair_type='网络',
                description='网线接口无信号', status='已完成',
                handler='admin', progress='已更换网线，恢复上网')

        self.stdout.write(self.style.SUCCESS('演示数据初始化完成！'))
