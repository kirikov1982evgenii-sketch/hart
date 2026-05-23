@echo off
chcp 65001 >nul
title Полный цикл: отклик + чаты + выполнение
cd /d "%~dp0"
set PY=%~dp0..\курсор\fl-orders-bot\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python

echo === 1. Сессия FL (если нужен вход — откроется Firefox) ===
"%PY%" "..\курсор\fl-orders-bot\export_fl_session.py" --wait 2>nul

echo.
echo === 2. Пакет откликов + чаты + выполнение (разово) ===
"%PY%" "..\курсор\fl-orders-bot\autopilot_full.py"

echo.
echo === 3. Постоянный мониторинг @workmy1bot ===
call start-freelance-agent.bat
