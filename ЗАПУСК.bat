@echo off
chcp 65001 >nul
cd /d "%~dp0"
title HART - не закрывайте это окно

where python >nul 2>&1
if errorlevel 1 (
  echo Python не найден. Установите с python.org и отметьте Add to PATH.
  start https://www.python.org/downloads/
  pause
  exit /b 1
)

python run.py
pause
