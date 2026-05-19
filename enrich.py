"""Обогащение карточек: id, программа, модули, уровень — без ухода с сайта."""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

LEVEL_BEGINNER = {"дети", "школа", "1-4", "базовый", "начальный"}
LEVEL_ADVANCED = {
    "вуз",
    "MIT",
    "алгоритмы",
    "ML",
    "AI",
    "Deep",
    "DevOps",
    "security",
    "статистика",
    "CS",
    "ERP",
}


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s)
    return (s[:72] or "course").strip("-")


def guess_level(tags: list[str], cat: str) -> str:
    tset = {t.lower() for t in tags}
    blob = " ".join(tags).lower()
    if tset & LEVEL_ADVANCED or any(x in blob for x in ("mit", "harvard", "stanford", "вуз")):
        return "Продвинутый"
    if tset & LEVEL_BEGINNER or cat == "interactive":
        return "Начальный"
    return "Средний"


def guess_duration(cat: str, tags: list[str]) -> str:
    if cat == "interactive":
        return "По теме урока · 30–90 мин"
    if cat == "methodology":
        return "Материалы · 1–3 часа"
    if "вуз" in tags or "MIT" in tags:
        return "Семестр · 40+ часов"
    if "видео" in tags:
        return "Видеокурс · 10–30 часов"
    if "IT" in tags or "Python" in tags:
        return "Трек · 20–60 часов"
    return "Самостоятельно · 15–40 часов"


def guess_format(cat: str) -> str:
    return {
        "interactive": "Интерактив и тренажёры",
        "methodology": "Методические материалы",
        "courses": "Онлайн-курс с модулями",
    }.get(cat, "Онлайн-обучение")


def provider_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    names = {
        "stepik.org": "Stepik",
        "openedu.ru": "Открытое образование",
        "resh.edu.ru": "РЭШ",
        "khanacademy.org": "Khan Academy",
        "coursera.org": "Coursera",
        "edx.org": "edX",
        "github.com": "GitHub",
        "learn.microsoft.com": "Microsoft Learn",
        "phet.colorado.edu": "PhET",
        "learningapps.org": "LearningApps",
        "geogebra.org": "GeoGebra",
        "kahoot.com": "Kahoot",
        "nearpod.com": "Nearpod",
        "h5p.org": "H5P",
    }
    for k, v in names.items():
        if k in host:
            return v
    return host.split(".")[0].capitalize() if host else "Партнёрская платформа"


def modules_for(r: dict) -> list[str]:
    title = r["title"]
    cat = r["cat"]
    if cat == "interactive":
        return [
            f"Обзор: возможности «{title}»",
            "Демонстрация и разбор типовых заданий",
            "Практика на уроке и самопроверка",
            "Рекомендации для домашнего закрепления",
        ]
    if cat == "methodology":
        return [
            "Цели урока и опорные материалы",
            "Практические задания для учеников",
            "Шаблоны оценивания и обратная связь",
            "Адаптация под свой класс и предмет",
        ]
    return [
        f"Введение в «{title}» и постановка целей",
        "Теория и разбор ключевых тем",
        "Практические задания и мини-проекты",
        "Итоги, чек-лист и дальнейшее развитие",
    ]


def learn_for(r: dict) -> list[str]:
    tags = r.get("tags") or []
    cat = r.get("cat", "courses")
    title = r["title"]
    if cat == "interactive":
        base = [
            f"Использовать «{title}» на уроке по назначению",
            "Подобрать задания под цель и уровень класса",
            "Встроить интерактив в сценарий урока",
        ]
    elif cat == "methodology":
        base = [
            "Применить материалы к своему предмету и классу",
            "Составить план урока на основе шаблонов",
            "Оценить результаты по понятным критериям",
        ]
    else:
        base = [
            f"Освоить ключевые темы курса «{title}»",
            "Применять знания на практических заданиях",
            "Ориентироваться в материалах партнёрской платформы",
        ]
    if "Python" in tags:
        base.insert(0, "Основы Python и типовые задачи")
    if "веб" in tags or "JS" in tags:
        base.insert(0, "Современная веб-разработка")
    if "ЕГЭ" in tags or "ОГЭ" in tags:
        base.insert(0, "Подготовка к экзамену по предмету")
    if "AI" in tags or "ML" in tags:
        base.insert(0, "Базовые модели машинного обучения")
    return base[:5]


def about_for(r: dict, provider: str, level: str) -> str:
    desc = (r.get("desc") or "").strip()
    title = r["title"]
    cat = r["cat"]
    lvl = level.lower()

    if len(desc) < 20 and cat == "courses":
        desc = f"Программа «{title}» — материалы для самостоятельного обучения."

    if cat == "interactive":
        return (
            f"{desc}\n\n"
            f"«{title}» — интерактивный ресурс ({provider}): задания и симуляции для урока. "
            f"На сайте «Клуб знаний HART» — описание, цели и структура работы. "
            f"Ссылка на платформу откроется в личном кабинете после оплаты ({lvl} уровень)."
        )
    if cat == "methodology":
        return (
            f"{desc}\n\n"
            f"Методические материалы «{title}» ({provider}): планы, шаблоны и задания к урокам. "
            f"На «Клуб знаний HART» — полная карточка программы. "
            f"Доступ к материалам — после подтверждения оплаты ({lvl} уровень)."
        )
    focus = desc if len(desc) > 30 else f"Курс «{title}»"
    return (
        f"{focus}\n\n"
        f"Программа на базе материалов {provider}: теория, практика и рекомендации по прохождению. "
        f"На «Клуб знаний HART» — модули, формат и цели обучения. "
        f"Ссылка на обучение откроется после подтверждения оплаты ({lvl} уровень)."
    )


def enrich_resource(r: dict, used_slugs: set[str]) -> dict:
    rid = slugify(r["title"])
    if rid in used_slugs:
        rid = f"{rid}-{hashlib.md5(r['url'].encode()).hexdigest()[:6]}"
    used_slugs.add(rid)
    tags = list(r.get("tags") or [])
    cat = r["cat"]
    provider = provider_from_url(r.get("url", ""))
    level = guess_level(tags, cat)
    duration = guess_duration(cat, tags)
    fmt = guess_format(cat)
    return {
        **r,
        "id": rid,
        "level": level,
        "duration": duration,
        "format": fmt,
        "provider": provider,
        "modules": modules_for(r),
        "learn": learn_for(r),
        "about": about_for(r, provider, level),
    }


def enrich_premium(r: dict, used_slugs: set[str]) -> dict:
    """Премиум-курс с готовыми модулями и описанием."""
    rid = r.get("id") or slugify(r["title"])
    if rid in used_slugs:
        rid = f"{rid}-{hashlib.md5(r['url'].encode()).hexdigest()[:6]}"
    used_slugs.add(rid)
    return {
        **r,
        "cat": r.get("cat", "courses"),
        "id": rid,
        "level": r.get("level", "Продвинутый"),
        "duration": r.get("duration", "Интенсив · 40+ часов"),
        "format": r.get("format", "Программа HART"),
        "provider": r.get("provider", "Клуб знаний HART"),
        "modules": list(r.get("modules", [])),
        "learn": list(r.get("learn", [])),
        "about": r.get("about", r.get("desc", "")),
        "featured": r.get("featured", False),
        "premium": True,
    }


def enrich_all(resources: list[dict]) -> list[dict]:
    used: set[str] = set()
    return [enrich_resource(r, used) for r in resources]
