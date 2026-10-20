@echo off
cd /d "%~dp0"
title Dormitory Management System
echo ============================================
echo   Dormitory Management System (A02)
echo   URL: http://127.0.0.1:8000
echo   Admin:    admin / admin123
echo   Student:  student1 / student123
echo ============================================
echo.
echo Starting server, please wait a few seconds...
echo.
start /b py manage.py runserver 127.0.0.1:8000
timeout /t 5 /nobreak >nul
start "" http://127.0.0.1:8000
echo.
echo ============================================
echo   Server is running! Browser opened.
echo   Close THIS window to stop the server.
echo ============================================
echo.
pause
