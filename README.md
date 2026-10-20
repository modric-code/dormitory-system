# 校园宿舍综合管理系统（A02）

基于 Python + Django + SQLite + Bootstrap 的课程设计项目。

## 功能
学生入住、宿舍分配、调宿管理、宿舍查询、维修申请、维修进度、宿舍信息统计。

## 快速启动
1. pip install -r requirements.txt
2. python manage.py makemigrations dormitory
3. python manage.py migrate
4. python manage.py init_data     # 初始化管理员与演示数据
5. python manage.py runserver
6. 浏览器访问 http://127.0.0.1:8000
   管理员：admin / admin123
   学生：student1 / student123
