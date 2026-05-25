#!/usr/bin/env python3
"""Короткие уроки: видео RuTube + факты + практика — без воды и робо-озвучки."""
from __future__ import annotations

from product_facts import BY_ID, PROVIDER_SHEET  # noqa: E402
from video_map import DEFAULT_RUTUBE, normalize_rutube_id  # noqa: E402

# Ротация образовательных роликов RuTube (работают в РФ)
MODULE_RUTUBE_POOL = [
    "68167787cf429b74f3d774a1108bd74f",
    "7a22453e4ff369e7dbc6e8865b62674c",
    "e14f344592fed5ab617689cda21cba66",
    "adb50fc6689e8c2159307373313a616a",
]


def _seed(*parts) -> int:
    import hashlib
    return int(hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()[:8], 16)


def rutube_for_module(course: dict, mod_idx: int) -> str:
    from video_map import COURSE_RUTUBE, videos_for_course

    cid = course.get("id", "")
    pool: list[str] = []
    if cid in COURSE_RUTUBE:
        pool.append(COURSE_RUTUBE[cid][0])
    for spec in videos_for_course(course):
        rid = normalize_rutube_id(spec.get("rutubeId") or "")
        if rid and rid not in pool:
            pool.append(rid)
    for rid in MODULE_RUTUBE_POOL:
        if rid not in pool:
            pool.append(rid)
    if not pool:
        return DEFAULT_RUTUBE[0]
    return pool[_seed(cid, mod_idx) % len(pool)]


_GENERIC_MARKERS = (
    "теория по теме урока",
    "ключевые понятия и определения",
    "введение:",
    "модуль ",
    "отработка темы на практике",
    "— часть ",
)


def _skip_topic(topic: str) -> bool:
    t = topic.strip().lower()
    if not t or "http" in t or t.startswith("ссылка:"):
        return True
    return any(m in t for m in _GENERIC_MARKERS)


def build_points(course: dict, topics: list[str], mod_idx: int) -> list[str]:
    cid = course.get("id", "")
    kb = BY_ID.get(cid, {})
    points: list[str] = []

    if mod_idx == 0 and kb.get("what"):
        points.append(kb["what"])

    for f in kb.get("features") or []:
        if len(points) >= 6:
            break
        points.append(f)

    if len(points) < 4 and kb.get("how"):
        for h in kb["how"][: 4 - len(points)]:
            points.append(h)

    prov = course.get("provider", "")
    if len(points) < 5 and prov in PROVIDER_SHEET:
        points.append(PROVIDER_SHEET[prov][_seed(cid, mod_idx) % len(PROVIDER_SHEET[prov])])

    for t in topics:
        if _skip_topic(t):
            continue
        if len(points) >= 8:
            break
        if t not in points:
            points.append(t.strip())

    if mod_idx == 0 and kb.get("for_whom"):
        points.append(f"Для кого: {kb['for_whom']}")
    if kb.get("limits") and mod_idx % 3 == 0:
        points.append(f"Важно: {kb['limits']}")

    if len(points) < 3:
        desc = (course.get("desc") or "").strip()
        if desc:
            points.append(desc)
        prov = course.get("provider", "")
        if prov:
            points.append(f"Платформа: {prov} — выполняйте задания по правилам курса на сайте партнёра.")
        points.append(f"Блок {mod_idx + 1}: закрепите материал по чек-листу урока.")

    return points[:8]


def build_summary(course: dict, mod_title: str, mod_idx: int, hours: int) -> str:
    title = course.get("title", "Программа")
    num = course.get("_catalog_index", "")
    prefix = f"Курс №{num} · " if num else ""
    return (
        f"{prefix}«{mod_title}» — {hours} ч. Смотрите видео, затем закрепите "
        f"по пунктам и выполните задание. Программа «{title}»."
    )


def build_module_lesson(
    course: dict,
    mod_title: str,
    hours: int,
    topics: list[str],
    mod_idx: int,
) -> dict:
    cid = course.get("id", "course")
    points = build_points(course, topics, mod_idx)
    rid = rutube_for_module(course, mod_idx)

    return {
        "id": f"{cid}-mod-{mod_idx:02d}",
        "title": f"Урок {mod_idx + 1}: {mod_title}",
        "type": "lesson",
        "duration": f"{hours} ч",
        "hours": hours,
        "rutubeId": rid,
        "summary": build_summary(course, mod_title, mod_idx, hours),
        "points": points,
        "tasks": _tasks(course, mod_title, hours),
    }


def _tasks(course: dict, mod_title: str, hours: int) -> list[dict]:
    from supplementary_materials import enrich_tasks_extra

    base = [
        {
            "title": "После видео",
            "instruction": f"По «{mod_title}»: выпишите 5 тезисов из ролика и сопоставьте с пунктами урока.",
        },
        {
            "title": "Практика",
            "instruction": f"Выполните одно задание по теме (~{max(1, hours // 3)} ч). Краткий отчёт — 15–20 предложений.",
        },
    ]
    return base + enrich_tasks_extra(course, mod_title, hours)
