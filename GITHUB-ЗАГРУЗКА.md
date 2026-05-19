# Как залить эту папку на GitHub

**Имя репозитория (рекомендуется):** `klub-znaniy-hart` или `hart-knowledge-club`  
**Описание репозитория:** `Клуб знаний HART — каталог курсов, оплата, Telegram-бот`

## Через сайт github.com

1. [github.com/new](https://github.com/new) → имя репозитория → **Create repository**
2. На странице репозитория: **uploading an existing file**
3. Перетащите **все файлы из этой папки** (не саму папку целиком, а содержимое)
4. Commit message: `Первый коммит — Клуб знаний HART`
5. **Commit changes**

## Через Git (если установлен)

```bat
cd /d "C:\Users\Falcoone\Desktop\Клуб-знаний-HART-GitHub"
git init
git add .
git commit -m "Клуб знаний HART — каталог и оплата"
git branch -M main
git remote add origin https://github.com/ВАШ_ЛОГИН/klub-znaniy-hart.git
git push -u origin main
```

## Не загружайте

- `.env.local` — токены бота и PIN админа
- Скрины чеков из `data/receipts/`

После загрузки следуйте **DEPLOY.md** для публикации сайта в интернет.
