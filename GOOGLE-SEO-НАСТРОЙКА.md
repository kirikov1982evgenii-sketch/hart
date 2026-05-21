# Google и Yandex: как начать находить сайт

Сайт: **http://hart-club.ru** (работает стабильно). HTTPS на GitHub Pages пока не принудительный.

## Уже сделано автоматически (21.05.2026)

- **IndexNow → Яндекс:** отправлены **235 URL** из sitemap (`success: true`)
- **sitemap.xml** и **robots.txt** на сайте, карта в robots
- **Деплой GitHub Pages** запущен, файлы IndexNow на сайте
- **API просмотров** на PythonAnywhere обновлён (`/api/views`)
- Открыты вкладки Google Search Console и Яндекс.Вебмастер (если браузер на ПК)

## Осталось только с вашим входом в Google (5 мин)

Google **не даёт** подтвердить домен без входа в ваш аккаунт Google. Нужен один раз TXT в REG.RU или файл `regru-api.txt` на рабочем столе (см. `regru-api-СОЗДАТЬ.txt`).

## 1. Google Search Console (Европа, США)

1. Откройте [Google Search Console](https://search.google.com/search-console).
2. **Добавить ресурс** → тип **Домен** → `hart-club.ru`.
3. Подтвердите домен в REG.RU: запись **TXT** (Google покажет значение).
4. После проверки: **Файлы Sitemap** → добавить  
   `https://hart-club.ru/sitemap.xml`
5. **Проверка URL** → вставьте `https://hart-club.ru/` → **Запросить индексирование**.

Индексация обычно **2–8 недель**. В англоязычном Google помогают страницы с `?lang=en` и английские заголовки (уже настроены на сайте).

## 2. Яндекс.Вебмастер (Россия)

1. [webmaster.yandex.ru](https://webmaster.yandex.ru) → добавить `hart-club.ru`.
2. Подтверждение: meta-тег или DNS (как подскажет Яндекс).
3. **Индексирование** → **Файлы Sitemap** → `https://hart-club.ru/sitemap.xml`.

## 3. HTTPS

GitHub → репозиторий **hart** → **Settings** → **Pages** → включить **Enforce HTTPS**, когда кнопка станет активной (после выпуска сертификата для домена).

## 4. Что уже сделано в коде

- `sitemap.xml` — главная, поддержка, оплата, **231+** страниц курсов
- `robots.txt` — карта сайта, закрыты кабинет и админка
- **hreflang** ru / en на главной и при смене языка
- Английские **title** и **description** для Google (EU/US)
- Параметр `?lang=en` для английской версии

## 5. Ускорить появление в поиске

- Делитесь ссылкой в Telegram, VK, WhatsApp (кнопки на главной).
- Добавьте сайт в подпись, канал, профиль FL.ru.
- Не ждите топ по запросу «online courses» без рекламы и ссылок — конкуренция очень высокая.

## 6. Яндекс.Метрика (по желанию)

В GitHub: **Settings** → **Secrets and variables** → **Variables** →  
`HART_YANDEX_METRIKA_ID` = номер счётчика с [metrika.yandex.ru](https://metrika.yandex.ru).
