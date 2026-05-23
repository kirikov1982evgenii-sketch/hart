#!/usr/bin/env python3
"""Проверка качества курсов перед продажей."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "resources.json"

RUTUBE_RE = re.compile(r"^[a-f0-9]{32}$", re.I)
YT_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

GENERIC_PHRASES = [
    "отработка темы на практике",
    "теория по теме урока",
    "ключевые понятия и определения",
    "шаблон",
    "lorem",
    "TODO",
    "заглушка",
]

GENERIC_MODULE_TITLES = [
    "теория по теме урока — часть",
    "интерактив на платформе — часть",
]


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def audit():
    data = load()
    resources = data.get("resources") or []
    issues: list[str] = []
    stats = {
        "courses": len(resources),
        "lesson_modules": 0,
        "missing_rutube": 0,
        "short_points": 0,
        "generic_points": 0,
        "empty_summary": 0,
        "no_tasks": 0,
        "duplicate_rutube_only": 0,
        "generic_module_titles": 0,
    }

    for i, c in enumerate(resources):
        cid = c.get("id", f"#{i}")
        title = c.get("title", "")
        lessons = c.get("lessons") or []
        if not lessons:
            issues.append(f"[{cid}] нет уроков")
            continue

        mod_lessons = [l for l in lessons if l.get("type") == "lesson" or "-mod-" in str(l.get("id", ""))]
        if not mod_lessons:
            issues.append(f"[{cid}] «{title}»: нет модулей type=lesson")

        for l in mod_lessons:
            stats["lesson_modules"] += 1
            tlow = (l.get("title") or "").lower()
            if any(g in tlow for g in GENERIC_MODULE_TITLES):
                stats["generic_module_titles"] += 1
                if stats["generic_module_titles"] <= 15:
                    issues.append(f"[{cid}] устаревшее название модуля: {l.get('title')}")
            rid = (l.get("rutubeId") or "").strip()
            if not rid:
                stats["missing_rutube"] += 1
                issues.append(f"[{cid}] {l.get('id')}: нет rutubeId")
            elif not RUTUBE_RE.match(rid) and not YT_RE.match(rid):
                issues.append(f"[{cid}] {l.get('id')}: подозрительный rutubeId={rid!r}")

            pts = l.get("points") or []
            if len(pts) < 3:
                stats["short_points"] += 1
                if len(issues) < 80:
                    issues.append(f"[{cid}] {l.get('id')}: мало пунктов ({len(pts)})")

            for p in pts:
                pl = (p or "").lower()
                if any(g in pl for g in GENERIC_PHRASES):
                    stats["generic_points"] += 1

            if not (l.get("summary") or "").strip():
                stats["empty_summary"] += 1

            tasks = l.get("tasks") or []
            if not tasks:
                stats["no_tasks"] += 1

        # Первый модуль курса №1 и №135 — выборочно
        if cid in ("облако-знаний", "nptel-india", "microsoft-learn"):
            m0 = next((l for l in lessons if l.get("type") == "lesson"), None)
            if m0 and len(m0.get("points") or []) < 4:
                issues.append(f"[{cid}] слабый первый урок: points={m0.get('points')}")

    # Дубли rutube в одном курсе — не ошибка, но отметим
    for c in resources[:5]:
        rids = [l.get("rutubeId") for l in c.get("lessons") or [] if l.get("rutubeId")]
        if len(rids) > 2 and len(set(rids)) == 1:
            stats["duplicate_rutube_only"] += 1

    print("=== QA AUDIT ===")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"\nПроблем (показано до 40): {len(issues)}")
    for line in issues[:40]:
        print(" ", line)
    if len(issues) > 40:
        print(f"  ... ещё {len(issues) - 40}")
    return 1 if any(x.startswith("[") and "нет уроков" in x or "нет rutubeId" in x for x in issues) else 0


if __name__ == "__main__":
    sys.exit(audit())
