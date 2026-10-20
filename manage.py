#!/usr/bin/env python
"""Django 的命令行管理工具，用于启动服务、执行迁移、初始化数据等"""
import os
import sys


def main():
    """Django 项目入口函数"""
    # 设置项目配置模块
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dormitory_system.settings')
    try:
        # 从 Django 导入命令行执行器
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # 未安装 Django 时给出友好提示
        raise ImportError(
            "无法导入 Django，请确认已安装，并激活了虚拟环境。"
        ) from exc
    # 执行命令行参数
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
