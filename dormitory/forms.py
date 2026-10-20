"""表单定义：用于数据录入与校验，并统一套用 Bootstrap 样式"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Student, Dormitory, Room, CheckIn, TransferRecord, RepairRequest


class BootstrapFormMixin:
    """给所有表单控件统一添加 Bootstrap 样式类"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.DateInput):
                widget.attrs.setdefault('type', 'date')
                widget.attrs.setdefault('class', 'form-control')
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault('class', 'form-select')
            else:
                widget.attrs.setdefault('class', 'form-control')


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    """学生自助注册表单：同时创建用户账号与对应学生档案"""
    name = forms.CharField(label='姓名', max_length=30)
    student_no = forms.CharField(label='学号', max_length=20)
    gender = forms.ChoiceField(label='性别', choices=Student.GENDER_CHOICES)
    college = forms.CharField(label='学院', max_length=50, required=False)
    major = forms.CharField(label='专业', max_length=50, required=False)
    class_name = forms.CharField(label='班级', max_length=50, required=False)
    phone = forms.CharField(label='联系电话', max_length=20, required=False)

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def clean_student_no(self):
        """校验学号唯一"""
        sno = self.cleaned_data['student_no']
        if Student.objects.filter(student_no=sno).exists():
            raise forms.ValidationError('该学号已被注册！')
        return sno

    def save(self, commit=True):
        """保存用户并同步创建学生档案"""
        user = super().save(commit=False)
        user.role = 'student'
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
            Student.objects.create(
                user=user,
                student_no=self.cleaned_data['student_no'],
                name=self.cleaned_data['name'],
                gender=self.cleaned_data['gender'],
                college=self.cleaned_data.get('college', ''),
                major=self.cleaned_data.get('major', ''),
                class_name=self.cleaned_data.get('class_name', ''),
                phone=self.cleaned_data.get('phone', ''),
            )
        return user


class StudentForm(BootstrapFormMixin, forms.ModelForm):
    """学生信息表单"""
    class Meta:
        model = Student
        fields = ['student_no', 'name', 'gender', 'college', 'major', 'class_name', 'phone']


class DormitoryForm(BootstrapFormMixin, forms.ModelForm):
    """宿舍楼表单"""
    class Meta:
        model = Dormitory
        fields = ['name', 'floors', 'gender', 'manager', 'note']


class RoomForm(BootstrapFormMixin, forms.ModelForm):
    """房间表单"""
    class Meta:
        model = Room
        fields = ['dormitory', 'room_no', 'floor', 'bed_count', 'gender', 'status', 'note']


class CheckInForm(BootstrapFormMixin, forms.ModelForm):
    """入住登记表单"""
    class Meta:
        model = CheckIn
        fields = ['student', 'room', 'bed_no', 'checkin_date', 'note']


class TransferForm(BootstrapFormMixin, forms.ModelForm):
    """调宿表单"""
    class Meta:
        model = TransferRecord
        fields = ['student', 'to_room', 'reason', 'transfer_date']


class RepairForm(BootstrapFormMixin, forms.ModelForm):
    """报修申请表单"""
    class Meta:
        model = RepairRequest
        fields = ['repair_type', 'description']
