# Клуб знаний HART

Онлайн-каталог обучения: **231+ программ** (интерактивы, методички, курсы).  
Оплата **199 ₽** / **$4.99**, личный кабинет, Telegram-бот [@uportbot](https://t.me/uportbot).

## Стек

- Статический сайт (HTML, CSS, JavaScript)
- Python: API оплат, Telegram-бот
- Данные: `data/resources.json`, `data/i18n.json`

## Локальный запуск

```bat
start-site.bat
```

- Сайт: http://127.0.0.1:8765  
- API оплат: http://127.0.0.1:8766  

Секреты: скопируйте `.env.local.example` → `.env.local` (не в Git).

## Публикация в интернет

Подробно: **[DEPLOY.md](DEPLOY.md)**

| Часть | Хостинг |
|-------|---------|
| Сайт | Cloudflare Pages |
| API + бот | Render (`render.yaml`) |

## Структура

```
index.html          — каталог
pay.html            — оплата
cabinet.html        — личный кабинет
payment_server.py   — API оплат
telegram_bot.py     — бот Telegram
config.example.js   — шаблон настроек сайта
render.yaml         — деплой Render
```

## Лицензия

Приватный проект. Все права у владельца.
