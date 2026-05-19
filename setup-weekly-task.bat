@echo off
chcp 65001 >nul
cd /d "%~dp0"
set TASK_NAME=HART-Weekly-Courses
set PY=python
set SCRIPT=%~dp0weekly_add_courses.py

echo Регистрация задачи Windows: каждый понедельник в 10:00
schtasks /Create /TN "%TASK_NAME%" /TR "\"%PY%\" \"%SCRIPT%\"" /SC WEEKLY /D MON /ST 10:00 /F
if errorlevel 1 (
  echo Ошибка. Запустите от имени администратора.
  pause
  exit /b 1
)
echo Готово. Проверка вручную: python weekly_add_courses.py --force
pause
