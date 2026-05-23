#!/usr/bin/env python3
"""Генерация насыщенных программ 300–520+ часов: модули, шаги, задания, проекты."""
from __future__ import annotations

import re
from urllib.parse import urlparse

# id курса → список (название модуля, часы, подтемы)
CUSTOM_SYLLABI: dict[str, list[tuple[str, int, list[str]]]] = {
    "microsoft-learn": [
        ("Azure: облако и модели сервисов", 20, [
            "IaaS, PaaS, SaaS; регионы и пары availability zones",
            "Подписка, resource group, ARM-шаблоны",
            "Портал Azure, Cloud Shell, CLI az",
            "Стоимость: калькулятор, бюджеты, теги ресурсов",
            "Лаб: создать RG, storage, web app (Learn sandbox)",
        ]),
        ("Вычисления: VM, масштабирование, App Service", 20, [
            "Семейства VM, диски, сетевые интерфейсы",
            "Availability sets, scale sets, зоны",
            "App Service: планы, deployment slots",
            "Контейнеры: ACI vs AKS обзор",
            "Лаб: развернуть веб-приложение .NET на App Service",
        ]),
        ("Сеть Azure: VNet, NSG, балансировка", 20, [
            "VNet, подсети, peering",
            "NSG, Application Security Groups",
            "Load Balancer, Application Gateway",
            "VPN, ExpressRoute — когда что",
            "Лаб: VNet + VM + правила NSG",
        ]),
        ("Хранение: Blob, Files, Disk, синхронизация", 20, [
            "Storage account, redundancy (LRS/ZRS/GRS)",
            "Blob tiers: hot, cool, archive",
            "Azure Files, File Sync",
            "Backup и Site Recovery обзор",
            "Лаб: загрузка статики + SAS token",
        ]),
        ("Идентификация: Microsoft Entra ID", 20, [
            "Tenants, users, groups, licenses",
            "RBAC в Azure vs роли в Entra",
            "Conditional Access, MFA",
            "Managed identities для приложений",
            "Лаб: назначить RBAC на resource group",
        ]),
        ("Безопасность и соответствие", 20, [
            "Defender for Cloud, Secure Score",
            "Key Vault: секреты, ключи, сертификаты",
            "Policy, Blueprints (обзор)",
            "Zero Trust принципы в Azure",
            "Лаб: Key Vault + App Service reference",
        ]),
        ("Мониторинг и надёжность", 20, [
            "Azure Monitor, Log Analytics, alerts",
            "Application Insights для .NET",
            "Dashboards, workbooks",
            "SLA, SLO, планы восстановления",
            "Лаб: alert на CPU VM",
        ]),
        (".NET: экосистема и SDK", 20, [
            "CLR, .NET 8 SDK, solution structure",
            "NuGet, восстановление пакетов",
            "dotnet CLI: new, build, test, publish",
            "Кроссплатформенность Windows/Linux",
            "Проект: console app + unit test xUnit",
        ]),
        ("C#: синтаксис и типы", 20, [
            "Типы значений/ссылок, nullable",
            "LINQ, коллекции, async/await",
            "Обработка ошибок, logging",
            "records, pattern matching",
            "Проект: 5 мини-задач на Codewars/LeetCode Easy",
        ]),
        ("ООП и проектирование на C#", 20, [
            "Инкапсуляция, наследование, интерфейсы",
            "SOLID кратко, DI контейнер",
            "Паттерны: Repository, Factory",
            "Тестируемость, моки Moq",
            "Проект: слой данных + сервис",
        ]),
        ("ASP.NET Core Web API", 20, [
            "Minimal APIs vs controllers",
            "Middleware, routing, model binding",
            "JWT auth обзор, CORS",
            "OpenAPI/Swagger",
            "Проект: REST API CRUD + Swagger",
        ]),
        ("Entity Framework Core", 20, [
            "Code-first, migrations",
            "LINQ to Entities, Include",
            "Транзакции, производительность",
            "SQLite/SQL Server в Azure",
            "Проект: API + EF + SQL",
        ]),
        ("DevOps: GitHub Actions + Azure", 20, [
            "CI/CD pipeline YAML",
            "Deploy to App Service / Container Apps",
            "Infrastructure as Code: Bicep intro",
            "Секреты в pipeline",
            "Проект: auto-deploy при push main",
        ]),
        ("Контейнеры и Kubernetes (AKS) intro", 20, [
            "Dockerfile для .NET",
            "Azure Container Registry",
            "AKS кластер: nodes, pods, services",
            "Helm обзор",
            "Лаб: образ в ACR + deploy на AKS (Learn path)",
        ]),
        ("Данные в Azure", 20, [
            "SQL Database, Cosmos DB обзор",
            "Synapse / Fabric — роль аналитика",
            "Data Factory pipelines",
            "DP-900 темы: хранилища, ETL",
            "Лаб: Azure SQL + подключение из API",
        ]),
        ("AI + Azure OpenAI", 20, [
            "Cognitive Services обзор",
            "Azure OpenAI: deployments, prompts",
            "Responsible AI checklist",
            "RAG архитектура intro",
            "Лаб: вызов API из .NET (ключ в Key Vault)",
        ]),
        ("Power Platform для разработчика", 20, [
            "Power Apps canvas vs model-driven",
            "Power Automate flows",
            "Dataverse связь с Azure",
            "PL-900 темы",
            "Лаб: flow по email при событии",
        ]),
        ("Microsoft 365 admin", 20, [
            "Exchange Online, Teams admin",
            "SharePoint sites, OneDrive",
            "MS-900 темы лицензирования",
            "Graph API intro",
            "Чек-лист: подготовка к MS-900",
        ]),
        ("Подготовка AZ-900", 20, [
            "Повторение cloud + pricing + identity",
            "Пробные тесты MeasureUp/official practice",
            "Разбор 50 вопросов с объяснением",
            "Дата экзамена: регистрация Pearson VUE",
            "Итог: таблица пробелов",
        ]),
        ("Подготовка AZ-104", 20, [
            "VM, сеть, storage — углубление",
            "Backup, monitor, automate",
            "Практика: 3 полных лабораторных дня",
            "Пробный экзамен",
            "План сдачи",
        ]),
        ("Подготовка DP-900 / fundamentals data", 20, [
            "Реляционные vs нереляционные",
            "Lakehouse, warehouse",
            "Практика вопросов",
            "Связь с Synapse Learn modules",
            "Итоговый конспект",
        ]),
        ("Capstone: full-stack Azure app", 40, [
            "ТЗ: API + SPA + SQL + CI/CD + monitor",
            "Неделя 1: архитектура и IaC",
            "Неделя 2: backend + auth",
            "Неделя 3: frontend deploy + тесты",
            "Неделя 4: документация + демо видео 10 мин",
        ]),
        ("Карьера: профиль и сертификаты", 20, [
            "Microsoft Learn profile, XP, trophies",
            "LinkedIn skills + learning paths",
            "Резюме: проекты capstone",
            "Собеседование: типовые вопросы Azure/.NET",
            "План на 6 месяцев обучения",
        ]),
        ("Security Operations: Sentinel и защита", 20, [
            "Microsoft Sentinel workspace",
            "KQL запросы для инцидентов",
            "Defender XDR интеграция",
            "Playbooks automation",
            "Лаб: разбор алерта в Sentinel",
        ]),
        ("Итоговые mock exams и повторение", 20, [
            "Смешанный пробник 60 вопросов AZ-900/AZ-104",
            "Разбор ошибок по доменам",
            "Календарь сдачи экзаменов",
            "Чек-лист готовности",
            "Портфолио: 3 проекта + 2 сертификата в плане",
        ]),
    ],
    "hart-lang-python": [
        ("Среда и первая программа", 20, ["Python 3.11+, VS Code, venv", "REPL, скрипты, pip", "print, input, f-strings", "Git init, .gitignore", "Задачи: 10 задач на типы"]),
        ("Типы и структуры данных", 20, ["int/float/str/bool", "list, tuple, dict, set", "срезы, comprehensions", "copy vs deepcopy", "Задачи: обработка CSV"]),
        ("Управление потоком", 20, ["if/elif/else", "for, while, enumerate", "match/case", "exceptions", "Мини-проект: калькулятор CLI"]),
        ("Функции и модули", 20, ["def, *args, **kwargs", "lambda, map, filter", "пакеты, __init__", "документация docstring", "Проект: модуль utils"]),
        ("Файлы и ОС", 20, ["pathlib, open()", "json, csv", "subprocess intro", "logging", "Проект: лог-анализатор"]),
        ("ООП в Python", 20, ["class, @dataclass", "наследование, MRO", "магические методы", "ABC, protocols", "Проект: модель предметной области"]),
        ("Тестирование", 20, ["pytest, fixtures", "coverage", "TDD цикл", "mock patch", "Покрытие >80% мини-проекта"]),
        ("Стандартная библиотека углублённо", 20, ["datetime, zoneinfo", "collections, itertools", "functools, typing", "dataclasses vs pydantic intro", "Задачи: 15 задач stdlib"]),
        ("Веб: HTTP и requests", 20, ["REST, status codes", "requests sessions", "API keys env", "rate limit retry", "Клиент публичного API"]),
        ("FastAPI сервис", 20, ["routes, pydantic models", "dependency injection", "OpenAPI", "uvicorn deploy local", "API с 5 endpoints"]),
        ("Базы данных", 20, ["SQL basics SQLite", "SQLAlchemy ORM", "миграции Alembic", "транзакции", "CRUD API + DB"]),
        ("Асинхронность", 20, ["async/await", "aiohttp", "asyncio tasks", "когда не async", "Переписать клиент API на async"]),
        ("Data: pandas и визуализация", 20, ["DataFrame, read_csv", "groupby, merge", "matplotlib/seaborn", "jupyter workflow", "Отчёт по датасету Kaggle"]),
        ("ML intro: scikit-learn", 20, ["train/test split", "метрики classification", "pipeline", "overfitting", "Модель на tabular data"]),
        ("Парсинг и скрапинг этично", 20, ["BeautifulSoup", "robots.txt", "этика и ToS", "кэширование", "Парсер документации (разрешённой)"]),
        ("Упаковка и публикация", 20, ["pyproject.toml", "wheel, pip install", "venv в prod", "Docker для Python", "Образ API в Docker"]),
        ("Безопасность кода", 20, ["secrets env", "SQL injection", "bandit, pip-audit", "OWASP top 10 для API", "Аудит своего API"]),
        ("Производительность", 20, ["profiling cProfile", "big-O практика", "numpy vectorization intro", "кэш functools.lru_cache", "Оптимизация hot path"]),
        ("Capstone: SaaS MVP", 40, ["ТЗ продукта", "FastAPI + SQL + auth", "frontend static или HTMX", "CI GitHub Actions", "Демо + README"]),
        ("Собеседования Python", 20, ["50 задач LeetCode Medium mix", "system design lite", "поведенческие", "резюме GitHub", "План 90 дней"]),
    ],
    "hart-poker-mastery": [
        ("Правила Texas Hold'em и позиции", 40, [
            "2 карманные + 5 общих; лучшая рука из 7",
            "BTN, SB, BB, UTG — инициатива и диапазоны",
            "Кэш 20–40 BI; MTT 100+ BI",
            "Журнал 100 раздач с позицией и действием",
            "Тест: 20 вопросов по правилам",
        ]),
        ("Математика: equity, pot odds, MDF", 40, [
            "Ауты и правило 2/4",
            "Pot odds vs equity на флопе и тёрне",
            "Implied odds и reverse implied",
            "MDF против ставки 33/66/75%",
            "50 задач на расчёт в тренажёре",
        ]),
        ("Префлоп: RFI, 3-bet, 4-bet", 40, [
            "RFI-чарты по позиции 6-max",
            "3-bet value (QQ+, AK) и блеф A5s",
            "Колл 3-bet IP с парами и suited connectors",
            "4-bet поляризация",
            "Сессия 500 рук в трекере",
        ]),
        ("Постфлоп: c-bet, check-raise, баррели", 40, [
            "Частота c-bet: сухая vs мокрая доска",
            "Check-raise value и блеф",
            "Двойной/тройной баррель",
            "Размеры 33% / 66% / overbet",
            "Разбор 50 спотов в Equilab/GTO+",
        ]),
        ("Защита BB и игра OOP", 40, [
            "Защита BB шире с pot odds",
            "Float флоп IP",
            "Probe после чека агрессора",
            "Сужение диапазона OOP",
            "Дневник 20 сложных рук",
        ]),
        ("Эксплойт 6-max кэш", 40, [
            "Изоляция лимперов",
            "Против рекреа: оверколл, недоблеф",
            "Против регов: меньше блефов",
            "HUD: VPIP, PFR, 3bet, AF",
            "Review сессии 2 часа",
        ]),
        ("ICM и турниры", 40, [
            "ICM на бабле и финальном столе",
            "Пуш/фолд коротких стеков",
            "Bounty: шире коллы",
            "Калькулятор ICM",
            "Симуляция FT 30 раздач",
        ]),
        ("Психология и дисциплина", 40, [
            "Тильт и stop-loss",
            "Журнал эмоций + EV решений",
            "Перерыв каждые 60 мин",
            "A-game чек-лист",
            "План 30 дней практики",
        ]),
        ("GTO и солверы (введение)", 40, [
            "Баланс value/bluff",
            "Pio/GTO+ обзор",
            "Когда эксплойт важнее GTO на низких лимитах",
            "Префлоп-чарты GTO",
            "1 сессия разбора solver",
        ]),
        ("Live и online tells", 40, [
            "Тайминги и сайзинги",
            "Live physical tells",
            "Нотсы в HUD",
            "500 рук с пометками",
            "Итоговая таблица эксплойтов",
        ]),
        ("Банкролл-менеджмент", 40, [
            "Кэш: 30+ BI, откат при −5 BI",
            "MTT: не >5% банка на турнир",
            "Отдельный покер-банк",
            "Таблица лимитов",
            "План роста на 6 месяцев",
        ]),
        ("Экзамен HART: 50 раздач", 40, [
            "50 раздач с обоснованием",
            "Критерии +EV и ICM",
            "Разбор с чек-листом модулей 1–11",
            "Итоговый тест 30 вопросов",
            "Сертификат программы",
        ]),
    ],
}

IT_TRACK = [
    "Введение, цели, настройка среды",
    "Базовые концепции и терминология",
    "Практика: guided exercises",
    "Углубление: типовые паттерны",
    "Инструменты разработчика и отладка",
    "Работа с данными и API",
    "Тестирование и качество кода",
    "Безопасность и best practices",
    "Интеграция с облаком / деплой",
    "Мини-проект 1",
    "Мини-проект 2",
    "Code review и рефакторинг",
    "Производительность",
    "Документация и командная работа",
    "Подготовка к сертификации / экзамену",
    "Capstone: итоговый проект",
]

SCHOOL_TRACK = [
    "Теория по теме урока",
    "Разбор примеров",
    "Интерактив на платформе",
    "Самостоятельная практика",
    "Контрольные вопросы",
    "Проект / исследование",
    "Повторение и закрепление",
    "Подготовка к ОГЭ/ЕГЭ (если применимо)",
]


def target_hours(course: dict) -> int:
    cid = course.get("id", "")
    cat = course.get("cat", "courses")
    tags = {t.lower() for t in (course.get("tags") or [])}
    blob = " ".join(tags) + " " + (course.get("title") or "").lower()

    if cid in CUSTOM_SYLLABI:
        return sum(h for _, h, _ in CUSTOM_SYLLABI[cid])
    if cat == "interactive":
        return 80
    if cat == "methodology":
        return 48
    if course.get("premium"):
        return 400
    if any(x in blob for x in ("python", "it", "azure", ".net", "devops", "ml", "ai", "java", "javascript")):
        return 520
    if any(x in blob for x in ("вуз", "mit", "coursera", "edx", "stepik")):
        return 360
    if cat == "courses":
        return 320
    return 200


def _generic_modules(course: dict, total_h: int) -> list[tuple[str, int, list[str]]]:
    from provider_syllabi import syllabus_for_provider

    prov_plan = syllabus_for_provider(course, total_h)
    if prov_plan:
        return prov_plan

    title = course.get("title", "Программа")
    cat = course.get("cat", "courses")
    tags = course.get("tags") or []
    n = max(8, min(14, total_h // 25))
    h_each = max(10, total_h // n)
    track = IT_TRACK if cat == "courses" and ("IT" in tags or "Python" in tags) else SCHOOL_TRACK

    modules: list[tuple[str, int, list[str]]] = []
    for i in range(n):
        theme = track[i % len(track)]
        mod_title = f"{theme} — этап {i + 1}"
        topics = [
            f"Цель этапа в программе «{title}»",
            f"Ключевые действия и материалы (блок {i + 1})",
            f"Практика: упражнения (~{h_each // 3} ч)",
            f"Самопроверка и типичные ошибки",
            f"Итог этапа: что должно получиться",
        ]
        modules.append((mod_title, h_each, topics))
    return modules


def syllabus_for(course: dict) -> list[tuple[str, int, list[str]]]:
    cid = course.get("id", "")
    if cid in CUSTOM_SYLLABI:
        return CUSTOM_SYLLABI[cid]
    return _generic_modules(course, target_hours(course))


def _steps_from_topics(topics: list[str], hours: int) -> list[dict]:
    h_step = max(1, hours // max(len(topics), 1))
    steps = []
    for i, t in enumerate(topics):
        steps.append({
            "title": f"Шаг {i + 1} (~{h_step} ч)",
            "text": t,
        })
    steps.append({
        "title": "Итог модуля",
        "text": f"Закрепление: повторите материал, отметьте пробелы. Рекомендуемое время на модуль: {hours} ч.",
    })
    return steps


def lesson_module(course: dict, idx: int, mod_title: str, hours: int, topics: list[str]) -> dict:
    from compact_lessons import build_module_lesson

    return build_module_lesson(course, mod_title, hours, topics, idx)


def lesson_roadmap(course: dict, modules: list[tuple[str, int, list[str]]]) -> dict:
    cid = course.get("id", "course")
    total = sum(h for _, h, _ in modules)
    lines = [f"Полная программа: {total}+ часов", f"Модулей: {len(modules)}", ""]
    for i, (name, h, _) in enumerate(modules):
        lines.append(f"{i + 1}. {name} — {h} ч")
    return {
        "id": f"{cid}-roadmap",
        "title": f"Дорожная карта · {total}+ часов",
        "type": "text",
        "duration": f"{total} ч",
        "hours": total,
        "body": "\n\n".join(lines),
    }


def format_duration(course: dict, lesson_count: int, total_hours: int) -> str:
    return f"{total_hours}+ часов · {lesson_count} блоков · программа HART"

