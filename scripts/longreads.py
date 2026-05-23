#!/usr/bin/env python3
"""Уникальные лонгриды для каждого курса (231+) — только на сайте HART."""
from __future__ import annotations

import hashlib
import re
from typing import Callable

from product_facts import BY_ID, PROVIDER_SHEET  # noqa: E402


def _seed(*parts: str | int) -> int:
    raw = "|".join(str(p) for p in parts)
    return int(hashlib.md5(raw.encode("utf-8")).hexdigest()[:8], 16)


def _pick(pool: list[str], *parts: str | int) -> str:
    return pool[_seed(*parts) % len(pool)]


def _skip_topic(topic: str) -> bool:
    t = topic.strip().lower()
    if not t or "http://" in t or "https://" in t:
        return True
    if t.startswith("ссылка:"):
        return True
    return False


def _domain(course: dict) -> str:
    cat = course.get("cat", "courses")
    tags = " ".join(course.get("tags") or []).lower()
    title = (course.get("title") or "").lower()
    blob = tags + " " + title
    if cat == "interactive":
        return "interactive"
    if cat == "methodology":
        return "methodology"
    if any(x in blob for x in ("python", "java", "javascript", "it", "azure", ".net", "devops")):
        return "it"
    if any(x in blob for x in ("ml", "ai", "нейро", "data")):
        return "data"
    if any(x in blob for x in ("огэ", "егэ", "вуз", "фгос")):
        return "school"
    if any(x in blob for x in ("покер", "poker")):
        return "poker"
    return "general"


def _course_index(course: dict, fallback: int = 0) -> int:
    n = course.get("_catalog_index")
    if isinstance(n, int) and n > 0:
        return n
    return fallback


def _glossary(topic: str, course: dict, mod_idx: int, t_idx: int) -> list[tuple[str, str]]:
    title = course.get("title", "Программа")
    dom = _domain(course)
    terms: list[tuple[str, str]] = []
    words = re.findall(r"[а-яёa-z]{4,}", topic.lower(), re.I)
    core = (words[_seed(topic, 0) % max(len(words), 1)] if words else "тема")[:20]

    pools = {
        "interactive": [
            (f"Интерактив «{core}»", "Задание в браузере с мгновенной обратной связью ученику."),
            ("Сценарий урока", "Последовательность: ввод → демо → практика → разбор ошибок."),
            ("Обратная связь", "Комментарий ученику сразу после ответа, без ожидания проверки учителем."),
        ],
        "it": [
            (f"Компонент «{core}»", "Часть системы с чёткой зоной ответственности и интерфейсом."),
            ("Конфигурация", "Набор параметров, определяющих поведение среды или приложения."),
            ("Отказоустойчивость", "Способность системы продолжать работу при сбое отдельного узла."),
        ],
        "school": [
            (f"Понятие «{core}»", "Элемент программы, проверяемый на контрольных и экзаменах."),
            ("Критерий оценивания", "Правило, по которому засчитывается верный ответ."),
            ("Типовая задача", "Формулировка, повторяющаяся на ОГЭ/ЕГЭ с вариациями чисел."),
        ],
        "general": [
            (f"Термин «{core}»", f"Ключевое слово темы в курсе «{title}»."),
            ("Практический кейс", "Ситуация из работы или учёбы, где тема даёт измеримый результат."),
            ("Чек-лист", "Короткий список шагов для самопроверки после изучения."),
        ],
    }
    base = pools.get(dom, pools["general"])
    for i, pair in enumerate(base):
        if _seed(course.get("id"), mod_idx, t_idx, i) % 2 == 0:
            terms.append(pair)
    extra = _pick(
        [
            ("Входные данные", "Исходные факты, без которых нельзя принять решение."),
            ("Результат", "Измеримый итог: файл, отчёт, настройка, навык."),
            ("Риск", "Что пойдёт не так при игнорировании темы."),
        ],
        course.get("id"),
        mod_idx,
        "gloss",
    )
    terms.append(extra)
    return terms[:5]


def _scenario(course: dict, topic: str, mod_idx: int, t_idx: int) -> str:
    title = course.get("title", "")
    num = _course_index(course)
    roles = [
        f"учитель ведёт урок по «{title}»",
        f"студент проходит модуль {mod_idx + 1} курса №{num}",
        f"методист готовит занятие с опорой на «{topic[:40]}»",
        f"самоучитель осваивает программу «{title}» дома",
    ]
    role = _pick(roles, course.get("id"), mod_idx, t_idx, "role")
    problems = [
        "Нужно за 45 минут довести группу до понятного результата без сторонних сайтов.",
        "Нужно сдать внутренний тест по модулю с первого раза.",
        "Нужно внедрить тему в реальный урок уже на этой неделе.",
        "Нужно закрыть пробел, который мешает следующему модулю.",
    ]
    problem = _pick(problems, course.get("id"), mod_idx, "prob")
    steps = [
        "Сформулировать цель в одном предложении.",
        "Выписать 5 опорных терминов из раздела выше.",
        "Решить практическое задание из конца модуля.",
        "Сверить ответ с критериями самопроверки.",
    ]
    step = _pick(steps, course.get("id"), t_idx, "step")
    return (
        f"**Ситуация:** {role}. {problem}\n\n"
        f"**Ход решения:** {step} Затем — разбор типичной ошибки и исправление по чек-листу модуля."
    )


def _mistakes(topic: str, course: dict, mod_idx: int) -> str:
    errs = [
        "Пропуск определений и переход сразу к «галочкам» в чек-листе — без устойчивого понимания.",
        "Смешение похожих терминов; нужно сравнить их в таблице из двух колонок.",
        "Зубрёжка без применения: повторите мини-кейс вслух своими словами.",
        "Игнорирование ограничений среды (время, уровень класса, версия ПО).",
        "Однократное чтение вместо цикла: прочитать → законспектировать → применить → проверить.",
    ]
    e1 = _pick(errs, course.get("id"), mod_idx, topic, 1)
    e2 = _pick(errs, course.get("id"), mod_idx, topic, 2)
    fix = _pick(
        [
            "Выделите 20 минут на повторение только этого раздела.",
            "Сделайте одно упражнение письменно, без подсказок.",
            "Объясните тему другому человеку или в заметке «как для новичка».",
        ],
        course.get("id"),
        mod_idx,
        "fix",
    )
    return f"**Частые ошибки:** {e1} {e2}\n\n**Как исправить:** {fix}"


def _theory_block(topic: str, course: dict, mod_title: str, mod_idx: int, t_idx: int) -> str:
    cid = course.get("id", "")
    title = course.get("title", "Программа")
    desc = (course.get("desc") or "").strip()
    provider = course.get("provider", "")
    kb = BY_ID.get(cid, {})
    dom = _domain(course)

    intros = {
        "interactive": (
            f"В курсе «{title}» тема «{topic}» раскрывает, как встроить интерактив в урок: "
            f"от постановки цели до анализа ответов класса. Материал автономный — учиться можно только на HART."
        ),
        "it": (
            f"Модуль «{mod_title}» в программе «{title}»: блок «{topic}» даёт инженерное понимание — "
            f"не обзор ссылками, а связная теория, шаги и проверка результата."
        ),
        "school": (
            f"Для программы «{title}» раздел «{topic}» привязан к школьной логике: "
            f"определение → пример → задание → критерий оценивания."
        ),
        "general": (
            f"«{topic}» — часть {t_idx + 1} в модуле «{mod_title}» курса «{title}». "
            f"Лонгрид собран так, чтобы не открывать сторонние ресурсы."
        ),
    }
    intro_pool = intros.get(dom, intros["general"])
    parts = [intro_pool[_seed(cid, mod_idx, t_idx, "intro") % len(intro_pool)]]

    if kb.get("what"):
        parts.append(f"**Суть продукта:** {kb['what']}")
    if desc:
        parts.append(f"**О курсе:** {desc}")
    if provider and provider in PROVIDER_SHEET:
        line = PROVIDER_SHEET[provider][_seed(cid, mod_idx) % len(PROVIDER_SHEET[provider])]
        parts.append(f"**Контекст {provider}:** {line}")

    feat = kb.get("features") or []
    if feat:
        i = _seed(cid, mod_idx, t_idx) % len(feat)
        parts.append(f"**Возможность:** {feat[i]}")

    how = kb.get("how") or []
    if how:
        j = _seed(cid, mod_idx, t_idx, "how") % len(how)
        parts.append(f"**Практический шаг (методика):** {how[j]}")

    deep = _pick(
        [
            (
                f"Разверните тему «{topic}» в трёх уровнях: что это, зачем в «{title}», "
                f"как проверить, что вы освоили. На каждый уровень — один абзац в конспекте."
            ),
            (
                f"Сопоставьте «{topic}» с соседними темами модуля «{mod_title}»: "
                f"что приходит раньше, что позже, где типичная путаница."
            ),
            (
                f"Сформулируйте три вопроса по «{topic}», на которые вы должны уметь ответить "
                f"без подсказок к концу модуля."
            ),
        ],
        cid,
        mod_idx,
        t_idx,
        "deep",
    )
    parts.append(deep)

    limits = kb.get("limits")
    if limits:
        parts.append(f"**Ограничения и нюансы:** {limits}")

    return "\n\n".join(parts)


def _practice_block(topic: str, course: dict, mod_idx: int, hours: int) -> str:
    h = max(1, hours // 6)
    return (
        f"**Мини-задание по теме (~{h} ч):** "
        f"на основе «{topic}» выполните письменную работу: постановка задачи, решение, вывод. "
        f"Объём — не меньше 250 слов. Критерий зачёта: посторонний читатель поймёт суть без ваших устных пояснений."
    )


def expand_topic_longread(
    topic: str,
    course: dict,
    mod_title: str,
    mod_idx: int,
    t_idx: int,
    hours: int,
) -> str:
    """Уникальный лонгрид на одну подтему (~900–1400 слов)."""
    gloss = _glossary(topic, course, mod_idx, t_idx)
    gloss_txt = "\n".join(f"- **{k}:** {v}" for k, v in gloss)

    blocks = [
        _theory_block(topic, course, mod_title, mod_idx, t_idx),
        f"### Мини-глоссарий\n{gloss_txt}",
        _scenario(course, topic, mod_idx, t_idx),
        _mistakes(topic, course, mod_idx),
        _practice_block(topic, course, mod_idx, hours),
    ]
    return "\n\n".join(blocks)


def build_module_longread(
    course: dict,
    mod_title: str,
    hours: int,
    topics: list[str],
    mod_idx: int,
) -> str:
    title = course.get("title", "Программа")
    num = _course_index(course)
    cid = course.get("id", "")

    parts = [
        f"## Модуль {mod_idx + 1}: {mod_title}",
        (
            f"**Курс №{num}** · «{title}» · **{hours} ч** · "
            f"лонгрид HART (уникальный текст, id `{cid}`)"
        ),
        "",
        _pick(
            [
                f"Этот модуль — часть полной программы. Вы изучаете материал **на сайте**, без обязательных переходов. "
                f"Курс №{num} отличается от других: другие примеры, формулировки и акценты.",
                f"Модуль {mod_idx + 1} курса №{num} «{title}» выстроен как самостоятельная глава учебника: "
                f"теория, глоссарий, кейс, ошибки, практика.",
            ],
            cid,
            mod_idx,
            "modintro",
        ),
        "",
    ]

    n = 0
    for ti, topic in enumerate(topics):
        if _skip_topic(topic):
            continue
        n += 1
        parts.append(f"---\n\n### §{n}. {topic.strip()}\n")
        parts.append(expand_topic_longread(topic, course, mod_title, mod_idx, ti, hours))
        parts.append("")

    parts.append("### Итоговая самопроверка модуля")
    parts.append(
        f"1. Сформулируйте, чем модуль {mod_idx + 1} курса №{num} «{title}» отличается от обычного краткого конспекта.\n"
        f"2. Назовите три термина из глоссариев выше и дайте определения.\n"
        f"3. Опишите кейс: что было целью, что сделали, что получилось.\n"
        f"4. Укажите одну ошибку, которую вы могли бы допустить, и как вы её предотвратите.\n"
        f"5. Отметьте выполнение практики в чек-листе курса."
    )
    return "\n\n".join(parts)


def on_site_tasks(course: dict, mod_title: str, hours: int, mod_idx: int) -> list[dict]:
    num = _course_index(course)
    return [
        {
            "title": "Лонгрид-конспект",
            "instruction": (
                f"Курс №{num}, модуль «{mod_title}»: конспект **от 600 слов** по тексту урока выше "
                f"(своими словами, не копипаст)."
            ),
        },
        {
            "title": "Практика",
            "instruction": (
                f"Выполните мини-задания из всех § модуля (~{max(3, hours // 4)} ч). "
                f"Оформите в одном документе: задача → ход → результат."
            ),
        },
        {
            "title": "Рефлексия",
            "instruction": (
                "Ответьте на 5 вопросов из «Итоговой самопроверки» в конце модуля. "
                "Каждый ответ — минимум 3 предложения."
            ),
        },
    ]
