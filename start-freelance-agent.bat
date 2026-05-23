@echo off
chcp 65001 >nul
title Агент фриланса HART (@uportbot)
cd /d "%~dp0"
echo.
echo  Агент: отклик - чаты - выполнение работы
echo  FL.ru + весь мир, фильтр Cursor
echo  Оплата/предоплата: Т-Банк
echo  Бот: @workmy1bot — напишите /start
echo.
echo  ВАЖНО: не запускайте telegram_bot.py одновременно!
echo.
set PY=%~dp0..\курсор\fl-orders-bot\.venv\Scripts\python.exe
if not exist "%PY%" set PY=python
"%PY%" freelance_agent\start_agent.py
pause
