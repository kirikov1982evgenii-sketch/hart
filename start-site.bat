@echo off
chcp 65001 >nul
cd /d "%~dp0"
set DEV_LOCAL=1
set PYTHONIOENCODING=utf-8
echo.
echo  Клуб знаний HART
echo  Сайт:      http://localhost:8765
echo  Оплаты API: http://127.0.0.1:8766
echo  Кабинет:   cabinet.html
echo  Владелец:  owner.html
echo  Поддержка: support.html
echo  Оплата в боте: /pay в @uportbot
echo  Публикация:  см. DEPLOY.md
echo  Секреты:   .env.local
echo.
start http://localhost:8765
set PYTHONIOENCODING=utf-8
start /B python payment_server.py
start /B python telegram_bot.py
python site_server.py
