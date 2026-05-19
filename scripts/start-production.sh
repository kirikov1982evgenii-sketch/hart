#!/bin/sh
# Запуск на VPS (Linux). Перед этим: cp .env.local.example .env.local && nano .env.local
set -e
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
export BIND_HOST=0.0.0.0

if [ ! -f .env.local ]; then
  echo "Создайте .env.local из .env.local.example"
  exit 1
fi

# Подгрузка .env.local в окружение
set -a
# shellcheck disable=SC1091
. ./.env.local
set +a

python scripts/gen_config.py

mkdir -p data/receipts

echo "Сайт:      http://0.0.0.0:${SITE_PORT:-8765}"
echo "API оплат: http://0.0.0.0:${PAYMENT_API_PORT:-8766}"

python payment_server.py &
python telegram_bot.py &
exec python site_server.py
