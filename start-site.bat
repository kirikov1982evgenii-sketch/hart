@echo off
chcp 65001 >nul
cd /d "%~dp0"
title HART - не закрывайте это окно
where python >nul 2>&1
if errorlevel 1 (
  echo [ОШИБКА] Python не найден. Установите Python 3 с python.org
  pause
  exit /b 1
)
echo.
echo  Клуб знаний HART - запуск сервера...
echo  Не закрывайте это окно, пока смотрите сайт.
echo.
python run.py
echo.
echo Сервер остановлен.
pause
