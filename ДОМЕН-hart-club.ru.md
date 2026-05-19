# Домен hart-club.ru

**Сайт:** https://hart-club.ru

## DNS у регистратора (REG.RU, Timeweb, nic.ru и т.д.)

### Вариант 1 — основной адрес `hart-club.ru`

| Тип | Имя | Значение |
|-----|-----|----------|
| **A** | `@` | `185.199.108.153` |
| **A** | `@` | `185.199.109.153` |
| **A** | `@` | `185.199.110.153` |
| **A** | `@` | `185.199.111.153` |

### Вариант 2 — также `www.hart-club.ru`

| Тип | Имя | Значение |
|-----|-----|----------|
| **CNAME** | `www` | `kirikov1982evgenii-sketch.github.io` |

## GitHub

После push в репозитории есть файл `CNAME`.

1. https://github.com/kirikov1982evgenii-sketch/hart/settings/pages  
2. **Custom domain:** `hart-club.ru` → **Save**  
3. Включите **Enforce HTTPS** (когда DNS подтянется, 10–60 мин).

## Проверка

- https://hart-club.ru  
- https://hart-club.ru/api/health — нет (API на PythonAnywhere)

API: https://eg1982.pythonanywhere.com
