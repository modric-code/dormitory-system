"""
数据模型定义（Django ORM）
运行 migrate 后会自动在 SQLite 中生成对应的数据表，无需手写建表 SQL。
"""
from datetime import date
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """自定义用户模型：在 Django 自带用户基础上增加"角色"字段，实现管理员/学生权限管理"""
    ROLE_CHOICES = (
        ('admin', '管理员'),
        ('student', '学生'),
    )
    role = models.CharField('角色', max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField('联系电话', max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return f'{self.username}({self.get_role_display()})'


class Dormitory(models.Model):
    """宿舍楼"""
    GENDER_CHOICES = (('男', '男'), ('女', '女'))
    name = models.CharField('楼栋名称', max_length=50, unique=True)   # 唯一约束
    floors = models.IntegerField('楼层数', default=6)
    gender = models.CharField('楼栋类型', max_length=10, choices=GENDER_CHOICES, default='男')
    manager = models.CharField('宿管员', max_length=30, blank=True)
    note = models.TextField('备注', blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '宿舍楼'
        verbose_name_plural = '宿舍楼'

    def __str__(self):
        return self.name


class Room(models.Model):
    """房间（宿舍）"""
    STATUS_CHOICES = (
        ('空闲', '空闲'),       # 空闲 = 有空余床位可入住
        ('已满', '已满'),
        ('维修中', '维修中'),
    )
    dormitory = models.ForeignKey(          # 外键：所属楼栋（一对多）
        Dormitory, on_delete=models.CASCADE, related_name='rooms', verbose_name='所属楼栋'
    )
    room_no = models.CharField('房间号', max_length=20)
    floor = models.IntegerField('楼层', default=1)
    bed_count = models.IntegerField('床位总数', default=4)
    gender = models.CharField('入住性别', max_length=10, choices=Dormitory.GENDER_CHOICES, default='男')
    status = models.CharField('房间状态', max_length=10, choices=STATUS_CHOICES, default='空闲')
    note = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '房间'
        verbose_name_plural = '房间'
        unique_together = ('dormitory', 'room_no')   # 同一栋楼内房号唯一

    def __str__(self):
        return f'{self.dormitory.name}-{self.room_no}'

    @property
    def occupied_count(self):
        """当前在住人数（根据在住记录动态计算）"""
        return self.checkins.filter(status='在住').count()

    @property
    def free_beds(self):
        """空余床位数"""
        return max(self.bed_count - self.occupied_count, 0)


class Student(models.Model):
    """学生"""
    GENDER_CHOICES = (('男', '男'), ('女', '女'))
    STATUS_CHOICES = (('未入住', '未入住'), ('在住', '在住'))
    user = models.OneToOneField(            # 一对一：关联登录账号（可空）
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='student', verbose_name='关联登录账号'
    )
    student_no = models.CharField('学号', max_length=20, unique=True)   # 学号唯一
    name = models.CharField('姓名', max_length=30)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES, default='男')
    college = models.CharField('学院', max_length=50, blank=True)
    major = models.CharField('专业', max_length=50, blank=True)
    class_name = models.CharField('班级', max_length=50, blank=True)
    phone = models.CharField('联系电话', max_length=20, blank=True)
    status = models.CharField('住宿状态', max_length=10, choices=STATUS_CHOICES, default='未入住')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '学生'
        verbose_name_plural = '学生'

    def __str__(self):
        return f'{self.name}({self.student_no})'


class CheckIn(models.Model):
    """入住记录（宿舍分配）"""
    STATUS_CHOICES = (('在住', '在住'), ('已退宿', '已退宿'))
    student = models.ForeignKey(            # 外键：学生
        Student, on_delete=models.CASCADE, related_name='checkins', verbose_name='学生'
    )
    room = models.ForeignKey(               # 外键：房间
        Room, on_delete=models.CASCADE, related_name='checkins', verbose_name='房间'
    )
    bed_no = models.CharField('床位号', max_length=10, blank=True)
    checkin_date = models.DateField('入住日期', default=date.today)
    checkout_date = models.DateField('退宿日期', null=True, blank=True)
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default='在住')
    note = models.TextField('备注', blank=True)

    class Meta:
        verbose_name = '入住记录'
        verbose_name_plural = '入住记录'

    def __str__(self):
        return f'{self.student.name}-{self.room}'


class TransferRecord(models.Model):
    """调宿记录"""
    student = models.ForeignKey(            # 外键：学生
        Student, on_delete=models.CASCADE, related_name='transfers', verbose_name='学生'
    )
    from_room = models.ForeignKey(          # 外键：原房间
        Room, on_delete=models.SET_NULL, null=True,
        related_name='transfer_out', verbose_name='原房间'
    )
    to_room = models.ForeignKey(            # 外键：新房间
        Room, on_delete=models.SET_NULL, null=True,
        related_name='transfer_in', verbose_name='新房间'
    )
    reason = models.TextField('调宿原因', blank=True)
    transfer_date = models.DateField('调宿日期', default=date.today)
    operator = models.CharField('经办人', max_length=30, blank=True)

    class Meta:
        verbose_name = '调宿记录'
        verbose_name_plural = '调宿记录'

    def __str__(self):
        return f'{self.student.name}: {self.from_room} → {self.to_room}'


class RepairRequest(models.Model):
    """维修申请工单"""
    STATUS_CHOICES = (
        ('待处理', '待处理'),
        ('处理中', '处理中'),
        ('已完成', '已完成'),
        ('已驳回', '已驳回'),
    )
    TYPE_CHOICES = (
        ('水电', '水电'),
        ('家具', '家具'),
        ('门窗', '门窗'),
        ('网络', '网络'),
        ('其他', '其他'),
    )
    room = models.ForeignKey(               # 外键：报修房间
        Room, on_delete=models.CASCADE, related_name='repairs', verbose_name='报修房间'
    )
    applicant = models.ForeignKey(          # 外键：申请人（学生）
        Student, on_delete=models.CASCADE, related_name='repairs', verbose_name='申请人'
    )
    repair_type = models.CharField('报修类型', max_length=10, choices=TYPE_CHOICES, default='其他')
    description = models.TextField('问题描述')
    status = models.CharField('工单状态', max_length=10, choices=STATUS_CHOICES, default='待处理')
    apply_date = models.DateField('报修日期', default=date.today)
    handler = models.CharField('处理人', max_length=30, blank=True)
    progress = models.TextField('维修进度说明', blank=True)
    finish_date = models.DateField('完成日期', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '维修工单'
        verbose_name_plural = '维修工单'

    def __str__(self):
        return f'#{self.pk} {self.room}-{self.repair_type}'

    @property
    def order_no(self):
        """友好工单号"""
        return f'BX{self.pk:06d}'
