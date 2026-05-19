# Публикация «Клуб знаний HART»

Проект из трёх частей:

| Часть | Файлы | Где хостить |
|-------|--------|-------------|
| Сайт | HTML, CSS, JS, `data/resources.json` | **Cloudflare Pages** (бесплатно) |
| API оплат | `payment_server.py` | **Render** (бесплатно) |
| Telegram-бот | `telegram_bot.py` | **Render Worker** |

---

## Шаг 1. GitHub

1. Создайте репозиторий на [github.com](https://github.com).
2. Залейте папку проекта (без `.env.local` — он в `.gitignore`).
3. **Не публикуйте** слабые PIN и токены в коде.

---

## Шаг 2. API оплат + бот (Render)

1. Зарегистрируйтесь на [render.com](https://render.com).
2. **New → Blueprint** → подключите репозиторий → выберите `render.yaml`.
3. Render создаст два сервиса: `hart-payments` и `hart-telegram-bot`.
4. В **Environment** каждого сервиса задайте секреты (Sync: false):

| Переменная | Пример | Где взять |
|------------|--------|-----------|
| `MARKET_ADMIN_PIN` | длинный-пин | придумайте сами |
| `MARKET_OWNER_PIN` | длинный-пин | придумайте сами |
| `MARKET_PAY_SALT` | случайная-строка-32 | придумайте сами |
| `HART_TELEGRAM_BOT_TOKEN` | `123:ABC...` | [@BotFather](https://t.me/BotFather) |
| `HART_TELEGRAM_CHAT_ID` | `123456789` | [@userinfobot](https://t.me/userinfobot) |
| `HART_SITE_URL` | `https://ваш-сайт.pages.dev` | после шага 3 |
| `MARKET_PAYMENT_API` | `https://hart-payments.onrender.com` | URL сервиса hart-payments |
| `MARKET_CORS_ORIGINS` | `https://ваш-сайт.pages.dev` | URL сайта (через запятую, если несколько) |
| `MARKET_SUPPORT_EMAIL` | ваша почта | |
| `MARKET_PAYPAL_EMAIL` | ваша почта | |

5. Дождитесь деплоя. Проверка: откройте `https://hart-payments.onrender.com/api/health` — должно быть `{"ok":true}`.

**Важно:** на бесплатном Render сервис «засыпает»; первый запрос может идти 30–60 секунд.

---

## Шаг 3. Сайт (GitHub Pages — уже настроено)

В репозитории включён workflow **Deploy site (GitHub Pages)**.

- URL сайта: **https://kirikov1982evgenii-sketch.github.io/hart/**
- При каждом `git push` в `main` сайт пересобирается автоматически.

Проверка: **Settings → Pages → Build and deployment → Source: GitHub Actions**.

### Альтернатива: Cloudflare Pages

1. [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → Connect Git.
2. Репозиторий — тот же.
3. Настройки сборки:

| Поле | Значение |
|------|----------|
| Build command | `npm run build` или `python scripts/gen_config.py` |
| Build output directory | `/` (корень репозитория) |
| Root directory | `/` |

4. **Environment variables** (Production):

| Переменная | Значение |
|------------|----------|
| `HART_SITE_URL` | `https://ваш-проект.pages.dev` (после первого деплоя замените на реальный URL) |
| `MARKET_PAYMENT_API` | `https://hart-payments.onrender.com` |
| `HART_TELEGRAM_BOT_USERNAME` | `uportbot` |
| `MARKET_PAY_CARD` | `2200702158761978` |
| `MARKET_PAY_BANK` | `Т-Банк` |
| `MARKET_PAY_NAME` | `Евгений` |
| `MARKET_PRICE_RUB` | `199` |
| `MARKET_PRICE_USD` | `4.99` |
| `MARKET_SUPPORT_EMAIL` | ваша почта |
| `MARKET_OWNER_EMAIL` | ваша почта |

5. Deploy. Скрипт `gen_config.py` создаст `config.js` с правильными URL.
6. Вернитесь в Render и обновите `HART_SITE_URL` и `MARKET_CORS_ORIGINS` на финальный URL Pages.
7. **Redeploy** Cloudflare Pages (повторная сборка).

---

## Шаг 4. Проверка

- [ ] Сайт открывается по `https://…`
- [ ] Каталог грузится (231 программа)
- [ ] Оплата: регион РФ, карта, код PAY-…
- [ ] Чек отправляется без ошибки CORS
- [ ] В Telegram (ваш `CHAT_ID`) приходит заявка
- [ ] Бот @uportbot отвечает на `/pay`
- [ ] После `python scripts/agent_payments.py approve` курс в кабинете

---

## Локальная разработка

```bat
start-site.bat
```

или вручную с `DEV_LOCAL=1` (только localhost):

```bat
set DEV_LOCAL=1
python site_server.py
python payment_server.py
python telegram_bot.py
```

---

## VPS (всё на одном сервере)

```bash
git clone <ваш-репозиторий>
cd Свободный-Маркет-Интерактив
cp .env.local.example .env.local
# отредактируйте .env.local
chmod +x scripts/start-production.sh
./scripts/start-production.sh
```

Или Docker:

```bash
docker build -t hart-site .
docker run -d -p 8765:8765 -p 8766:8766 --env-file .env.local hart-site
```

На VPS в `.env.local` укажите:

```
BIND_HOST=0.0.0.0
HART_SITE_URL=https://ваш-домен.ru
MARKET_PAYMENT_API=https://ваш-домен.ru:8766
```

(лучше nginx + HTTPS на 443 и прокси на порты 8765/8766)

---

## Файлы проекта для деплоя

| Файл | Назначение |
|------|------------|
| `render.yaml` | Blueprint Render (API + бот) |
| `scripts/gen_config.py` | Генерация `config.js` на хостинге |
| `package.json` | `npm run build` для Cloudflare |
| `_headers` | Заголовки безопасности на Cloudflare Pages |
| `requirements.txt` | Python для Render |
| `server_common.py` | Порт `PORT` и `0.0.0.0` на хостинге |

---

## Частые проблемы

**CORS / оплата не отправляется** — в Render добавьте точный URL сайта в `MARKET_CORS_ORIGINS`.

**API недоступен** — проверьте `paymentApiUrl` в `config.js` (должен быть `https://`, не `localhost`).

**Бот молчит** — проверьте `HART_TELEGRAM_BOT_TOKEN` и что Worker `hart-telegram-bot` запущен.

**Данные пропали после перезапуска Render** — чеки на диске free-tier не сохраняются надёжно; для продакшена нужен VPS или внешнее хранилище.
