#!/usr/bin/env python3
"""Рабочие YouTube ID и замена битых ссылок."""
from __future__ import annotations

import re

# Битые / устаревшие ID → рабочие публичные ролики
ID_REPLACEMENTS: dict[str, str] = {
    "8gy-LXYXzL0": "AHqXuklsrnM",
    "kqtD5X2vXr0": "rfscUVx6sLU",
    "g7Os-Q7hdQc": "Z-JNyfHo3XE",
    "Z0x9KJ9h4qY": "jt3M56mokMU",
    "pa3A-9wlxy8": "NybHckcB86Y",
    "jw8fbGu9qvs": "jt3M56mokMU",
    "PkZNo7MFNFg": "eWRfhZUzrAc",
    "eIrMbPsr1kM": "rfscUVx6sLU",
    "HXV3zeQKqNY": "3JZ_D3X6p3k",
    "41TCQHwzlGk": "rfscUVx6sLU",
    "GvH0X1E2eYk": "jt3M56mokMU",
    "0nbYW1fH6t4": "jt3M56mokMU",
}

COURSE_VIDEOS: dict[str, tuple[str, str]] = {
    "microsoft-learn": ("AHqXuklsrnM", "Microsoft Azure Fundamentals — введение"),
    "hart-lang-python": ("rfscUVx6sLU", "Python — полный курс (freeCodeCamp)"),
    "hart-poker-mastery": ("Z-JNyfHo3XE", "Покер: основы Texas Hold'em"),
}

# RuTube — основной плеер для РФ (YouTube часто заблокирован)
COURSE_RUTUBE: dict[str, tuple[str, str]] = {
    "microsoft-learn": ("adb50fc6689e8c2159307373313a616a", "Azure: облако и основы (RuTube)"),
    "hart-lang-python": ("68167787cf429b74f3d774a1108bd74f", "Python — полный курс 15 ч (RuTube)"),
    "hart-poker-mastery": ("e14f344592fed5ab617689cda21cba66", "Обучающее видео (RuTube)"),
}

PROVIDER_RUTUBE: dict[str, tuple[str, str]] = {
    "Microsoft Learn": ("adb50fc6689e8c2159307373313a616a", "Azure Fundamentals (RuTube)"),
    "Stepik": ("7a22453e4ff369e7dbc6e8865b62674c", "Stepik — Python (RuTube)"),
    "Khan Academy": ("e14f344592fed5ab617689cda21cba66", "Программирование — введение (RuTube)"),
    "PhET": ("y1c9z2A6yIs", "PhET — на YouTube; см. также материалы на сайте"),
    "Nptel": ("7a22453e4ff369e7dbc6e8865b62674c", "Онлайн-курс — как проходить (RuTube)"),
    "Coursera": ("e14f344592fed5ab617689cda21cba66", "MOOC — эффективное обучение (RuTube)"),
    "Edx": ("7a22453e4ff369e7dbc6e8865b62674c", "Онлайн-обучение в вузе (RuTube)"),
    "Mit ocw": ("68167787cf429b74f3d774a1108bd74f", "Самостоятельное обучение (RuTube)"),
}

TAG_RUTUBE: list[tuple[str, str, str]] = [
    ("Python", "68167787cf429b74f3d774a1108bd74f", "Python — курс (RuTube)"),
    ("IT", "adb50fc6689e8c2159307373313a616a", "IT и Azure (RuTube)"),
]

DEFAULT_RUTUBE = ("68167787cf429b74f3d774a1108bd74f", "Обучающее видео (RuTube)")

PROVIDER_VIDEOS: dict[str, tuple[str, str]] = {
    "Microsoft Learn": ("AHqXuklsrnM", "Azure Fundamentals — старт обучения"),
    "Stepik": ("ihRZmgx9-RU", "Как учиться на Stepik"),
    "Coursera": ("EqnL6E0OPrI", "Онлайн-курсы — как проходить эффективно"),
    "Khan Academy": ("jt3M56mokMU", "Khan Academy — обзор платформы"),
    "Открытое образование": ("7DGfm7KYwBM", "Онлайн-обучение в вузе"),
    "PhET": ("y1c9z2A6yIs", "PhET — интерактивные симуляции"),
    "GeoGebra": ("s-r6FnZOzF4", "GeoGebra — динамическая математика"),
}

TAG_VIDEOS: list[tuple[str, str, str]] = [
    ("Python", "rfscUVx6sLU", "Python — обучающий курс"),
    ("IT", "AHqXuklsrnM", "IT и облако — введение"),
    ("веб", "zQn_I0Q-ySs", "Веб-разработка — основы"),
    ("JS", "zQn_I0Q-ySs", "JavaScript — введение"),
    ("ML", "7Ve7KMo6aUU", "Machine Learning — введение"),
    ("AI", "7Ve7KMo6aUU", "Искусственный интеллект — обзор"),
    ("ОГЭ", "jt3M56mokMU", "Подготовка к экзаменам"),
    ("ЕГЭ", "jt3M56mokMU", "Подготовка к экзаменам"),
]

CAT_VIDEOS: dict[str, tuple[str, str]] = {
    "interactive": ("NybHckcB86Y", "Интерактивное обучение — обзор"),
    "methodology": ("7DGfm7KYwBM", "Методика и планирование урока"),
    "courses": ("EqnL6E0OPrI", "Онлайн-курс — как проходить программу"),
}

YOUTUBE_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def normalize_youtube_id(raw: str) -> str:
    if not raw:
        return ""
    s = str(raw).strip()
    if YOUTUBE_ID_RE.match(s):
        yid = s
    else:
        m = re.search(r"(?:v=|/embed/|youtu\.be/)([a-zA-Z0-9_-]{11})", s)
        yid = m.group(1) if m else ""
    if not yid:
        return ""
    return ID_REPLACEMENTS.get(yid, yid)


def normalize_rutube_id(raw: str) -> str:
    if not raw:
        return ""
    s = str(raw).strip()
    m = re.search(r"rutube\.ru/(?:video|play/embed)/([a-f0-9]{32})", s, re.I)
    if m:
        return m.group(1)
    if re.match(r"^[a-f0-9]{32}$", s, re.I):
        return s
    return ""


def videos_for_course(course: dict) -> list[dict]:
    """Список видеоуроков: rutubeId (приоритет в РФ) + youtubeId."""
    cid = course.get("id", "")
    cat = course.get("cat", "courses")
    tags = course.get("tags") or []
    prov = course.get("provider", "")
    seen_yt: set[str] = set()
    out: list[dict] = []

    def push(title: str, youtube: str = "", rutube: str = "") -> None:
        yid = normalize_youtube_id(youtube) if youtube else ""
        rid = normalize_rutube_id(rutube) if rutube else ""
        if yid and yid in seen_yt:
            yid = ""
        if yid:
            seen_yt.add(yid)
        if not yid and not rid:
            return
        out.append({
            "title": title or "Видеоурок",
            "youtubeId": yid,
            "rutubeId": rid,
        })

    if cid in COURSE_RUTUBE:
        r, t = COURSE_RUTUBE[cid]
        y = COURSE_VIDEOS.get(cid, ("", ""))[0]
        push(t, y, r)
    elif cid in COURSE_VIDEOS:
        y, t = COURSE_VIDEOS[cid]
        push(t, y, "")

    if prov in PROVIDER_RUTUBE and not any(x.get("rutubeId") for x in out):
        r, t = PROVIDER_RUTUBE[prov]
        y = PROVIDER_VIDEOS.get(prov, ("", ""))[0]
        push(t, y, r)
    elif prov in PROVIDER_VIDEOS and not out:
        y, t = PROVIDER_VIDEOS[prov]
        push(t, y, "")

    for tag, r, t in TAG_RUTUBE:
        if tag in tags and not any(x.get("rutubeId") for x in out):
            y = next((y for tg, y, _ in TAG_VIDEOS if tg == tag), "")
            push(t, y, r)
            break

    for tag, y, t in TAG_VIDEOS:
        if tag in tags and len(out) < 2:
            push(t, y, "")

    for v in course.get("videos") or []:
        if isinstance(v, dict) and len(out) < 2:
            push(
                v.get("title", "Видеоурок"),
                v.get("youtubeId") or v.get("id") or "",
                v.get("rutubeId") or "",
            )

    if cat in CAT_VIDEOS and not out:
        y, t = CAT_VIDEOS[cat]
        push(t, y, DEFAULT_RUTUBE[0])

    if not out:
        y, t = CAT_VIDEOS.get("courses", ("rfscUVx6sLU", "Обучающее видео"))
        push(t, y, DEFAULT_RUTUBE[0])
    elif not any(x.get("rutubeId") for x in out):
        out[0]["rutubeId"] = DEFAULT_RUTUBE[0]

    return out
