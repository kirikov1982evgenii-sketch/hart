#!/usr/bin/env python3
"""Полезные материалы к каждой программе: справочники, документация, практика."""
from __future__ import annotations

import re
from urllib.parse import urlparse

# (заголовок, url, описание)
COMMON_HART = [
    ("Кабинет HART", "https://hart-club.ru/cabinet.html", "Ваши оплаченные программы и доступ."),
    ("Поддержка по оплате", "https://hart-club.ru/support.html", "Вопросы по оплате и доступу."),
    ("Telegram-бот", "https://t.me/uportbot", "Напоминания и помощь с оплатой."),
]

DOMAIN_LINKS: dict[str, list[tuple[str, str, str]]] = {
    "it": [
        ("MDN Web Docs", "https://developer.mozilla.org/ru/", "Справочник по HTML, CSS, JavaScript и веб-API."),
        ("Документация Python", "https://docs.python.org/3/", "Официальный tutorial и стандартная библиотека."),
        ("freeCodeCamp", "https://www.freecodecamp.org/", "Бесплатные треки по программированию."),
        ("GitHub Skills", "https://skills.github.com/", "Практика Git и GitHub Actions."),
        ("LeetCode", "https://leetcode.com/", "Задачи для подготовки к собеседованиям."),
    ],
    "data": [
        ("Kaggle Learn", "https://www.kaggle.com/learn", "Микрокурсы по ML и данным."),
        ("scikit-learn docs", "https://scikit-learn.org/stable/user_guide.html", "Документация и примеры."),
        ("Pandas", "https://pandas.pydata.org/docs/", "Работа с таблицами в Python."),
    ],
    "school": [
        ("РЭШ", "https://resh.edu.ru/", "Уроки и подготовка к ОГЭ/ЕГЭ."),
        ("ФИПИ", "https://fipi.ru/", "Открытый банк заданий экзаменов."),
        ("Российская электронная школа", "https://resh.edu.ru/", "Федеральные материалы по предметам."),
    ],
    "interactive": [
        ("PhET", "https://phet.colorado.edu/", "STEM-симуляции в браузере."),
        ("LearningApps", "https://learningapps.org/", "Мини-упражнения для урока."),
        ("Облако знаний", "https://oblakoz.ru/eor", "Интерактивы для 1–11 классов."),
    ],
    "methodology": [
        ("ФГОС", "https://fgos.ru/", "Федеральные государственные стандарты."),
        ("РБК Trends: EdTech", "https://trends.rbc.ru/trends/education/", "Обзоры методик и цифрового обучения."),
    ],
    "poker": [
        ("PokerStars School", "https://www.pokerstars.com/poker/school/", "Бесплатные уроки для начинающих."),
        ("Equilab", "https://www.pokerstrategy.com/equilab/", "Расчёт equity (калькулятор)."),
    ],
    "general": [
        ("Википедия", "https://ru.wikipedia.org/", "Базовые определения по теме."),
        ("Coursera", "https://www.coursera.org/", "Дополнительные курсы от вузов."),
        ("Stepik", "https://stepik.org/", "Русскоязычные курсы и задачи."),
    ],
}

PROVIDER_EXTRA: dict[str, list[tuple[str, str, str]]] = {
    "Microsoft Learn": [
        ("Microsoft Learn", "https://learn.microsoft.com/", "Официальные модули Azure и .NET."),
        ("Azure free account", "https://azure.microsoft.com/free/", "Песочница для лабораторных."),
    ],
    "Stepik": [
        ("Stepik", "https://stepik.org/catalog", "Каталог курсов и задач."),
    ],
    "Coursera": [
        ("Coursera", "https://www.coursera.org/", "Видеолекции и сертификаты партнёров."),
    ],
    "Khan Academy": [
        ("Khan Academy", "https://www.khanacademy.org/", "Математика и науки на русском/англ."),
    ],
    "edX": [
        ("edX", "https://www.edx.org/", "Курсы MIT, Harvard и др."),
    ],
}


def _domain(course: dict) -> str:
    tags = " ".join(course.get("tags") or []).lower()
    title = (course.get("title") or "").lower()
    blob = tags + " " + title
    if course.get("cat") == "interactive":
        return "interactive"
    if course.get("cat") == "methodology":
        return "methodology"
    if "poker" in blob:
        return "poker"
    if any(x in blob for x in ("python", "java", "javascript", "typescript", "devops", "azure", ".net", "api")):
        return "it"
    if any(x in blob for x in ("ml", "data", "нейро", "анализ данных")):
        return "data"
    if any(x in blob for x in ("огэ", "егэ", "фгос", "школ", "1-11", "1–11")):
        return "school"
    return "general"


def _partner_link(course: dict) -> tuple[str, str, str] | None:
    url = (course.get("partnerUrl") or course.get("url") or "").strip()
    if not url.startswith("http"):
        return None
    host = urlparse(url).netloc.replace("www.", "")
    prov = course.get("provider") or host
    return (f"Платформа: {prov}", url, "Официальный сайт программы и сертификация.")


def collect_links(course: dict) -> list[tuple[str, str, str]]:
    seen: set[str] = set()
    out: list[tuple[str, str, str]] = []

    def add(title: str, url: str, desc: str) -> None:
        if url in seen:
            return
        seen.add(url)
        out.append((title, url, desc))

    for block in (COMMON_HART, DOMAIN_LINKS.get(_domain(course), []), PROVIDER_EXTRA.get(course.get("provider", ""), [])):
        for t, u, d in block:
            add(t, u, d)

    pl = _partner_link(course)
    if pl:
        add(*pl)

    modules = course.get("modules") or []
    if modules:
        add(
            "Конспект модуля",
            "https://hart-club.ru/course.html?id=" + (course.get("id") or "") + "&learn=1",
            f"Пройдите {len(modules)} модулей в плеере HART.",
        )

    return out[:12]


def materials_body(course: dict) -> str:
    title = course.get("title", "Программа")
    lines = [
        f"Подборка к программе «{title}»: документация, практика и официальные источники.",
        "",
        "## Рекомендуемый порядок",
        "",
        "1. Пройдите дорожную карту и модули в плеере HART.",
        "2. Выполните задания после каждого видеоурока.",
        "3. Используйте ссылки ниже для углубления и справки.",
        "4. Завершите итоговый тест программы.",
        "",
        "## Ссылки и инструменты",
        "",
    ]
    for name, url, desc in collect_links(course):
        lines.append(f"- {name} — {desc} Ссылка: {url}")
    lines.extend(
        [
            "",
            "## Шаблон конспекта",
            "",
            "- Цель урока и 3 ключевых термина",
            "- Пример из видео / платформы",
            "- Одна ошибка, которую вы исправили на практике",
            "- Вопрос для уточнения (форум, чат, преподаватель)",
            "",
            "## Самопроверка перед тестом",
            "",
            "- Могу объяснить тему своими словами 2–3 минуты",
            "- Выполнил(а) минимум 70% практических заданий",
            "- Повторил(а) слабые места по чек-листу модулей",
        ]
    )
    return "\n".join(lines)


def supplementary_lesson(course: dict) -> dict:
    cid = course.get("id") or "course"
    return {
        "id": f"{cid}-materials",
        "title": "Полезные материалы и шаблоны",
        "type": "content",
        "duration": "30–45 мин",
        "body": materials_body(course),
    }


def enrich_tasks_extra(course: dict, mod_title: str, hours: int) -> list[dict]:
    """Дополнительное задание к модулю."""
    partner = (course.get("partnerUrl") or "").strip()
    tasks = [
        {
            "title": "Самопроверка",
            "instruction": (
                f"По модулю «{mod_title}»: составьте 5 вопросов с ответами "
                f"и отметьте, что осталось непонятным (~{max(1, hours // 4)} ч)."
            ),
        },
    ]
    if partner.startswith("http"):
        tasks.append(
            {
                "title": "Платформа партнёра",
                "instruction": "Выполните одно задание на официальной платформе и кратко опишите результат.",
                "kind": "link",
                "url": partner,
            }
        )
    return tasks
