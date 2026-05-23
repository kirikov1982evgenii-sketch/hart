#!/usr/bin/env python3
"""Уроки 300–520+ часов: дорожная карта, модули со шагами и заданиями."""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from curriculum_500h import (  # noqa: E402
    format_duration,
    lesson_module,
    lesson_roadmap,
    syllabus_for,
    target_hours,
)
from product_facts import clean_about, product_sheet, quiz_from_sheet  # noqa: E402
from video_map import videos_for_course  # noqa: E402

RES = BASE / "data" / "resources.json"
BACKUP = BASE / "data" / "resources.backup.json"
CATALOG = BASE / "data" / "catalog.json"


def lesson_facts(cid: str, rows: list[tuple[str, str]]) -> dict:
    return {
        "id": f"{cid}-facts",
        "title": "Справка о продукте",
        "type": "facts",
        "duration": "15–20 мин",
        "facts": [{"label": k, "value": v} for k, v in rows],
    }


def lesson_paid_info(cid: str, course: dict, total_h: int) -> dict:
    title = course.get("title", "Программа")
    partner = course.get("partnerUrl") or course.get("url", "")
    return {
        "id": f"{cid}-paid",
        "title": "Что даёт оплата 199 ₽ в HART",
        "type": "facts",
        "duration": "5 мин",
        "facts": [
            {"label": "Программа", "value": f"«{title}» — {total_h}+ часов: дорожная карта, модули, задания, тесты"},
            {"label": "На сайте HART", "value": "Дорожная карта, конспект по модулям, задания и тест — основная работа на hart-club.ru"},
            {"label": "Личный кабинет", "value": "Доступ после оплаты 199 ₽; прогресс заданий сохраняется в браузере"},
            {"label": "Формат", "value": "Видео (RuTube) + пункты урока + практика; партнёрская платформа — по ссылке в справке"},
            {"label": "Видео", "value": "Обучающие ролики RuTube встроены в урок; тема курса — в конспекте и заданиях"},
        ],
    }


def lesson_video(cid: str, spec: dict, index: int = 0) -> dict:
    suffix = f"-video-{index}" if index else "-video"
    lesson = {
        "id": f"{cid}{suffix}",
        "title": spec.get("title", "Видеоурок"),
        "type": "video",
        "duration": "30–90 мин",
    }
    if spec.get("rutubeId"):
        lesson["rutubeId"] = spec["rutubeId"]
    if spec.get("youtubeId"):
        lesson["youtubeId"] = spec["youtubeId"]
    return lesson


def lesson_embed(cid: str, url: str) -> dict | None:
    if not url or not url.startswith("http"):
        return None
    return {
        "id": f"{cid}-embed",
        "title": "Практика на платформе партнёра",
        "type": "embed",
        "duration": "по модулю",
        "embedUrl": url,
        "hint": "Выполняйте лабораторные и тесты на платформе. Если не загружается — откройте в новой вкладке.",
    }


def enrich_resource(r: dict) -> dict:
    cid = r.get("id") or "course"
    total_h = target_hours(r)
    modules_spec = syllabus_for(r)
    rows = product_sheet(r)
    # обновить объём в справке
    rows = [(k, v if k != "Объём программы" else f"{total_h}+ часов · {len(modules_spec)} модулей") for k, v in rows]

    lessons: list[dict] = [lesson_facts(cid, rows)]

    lessons.extend([
        lesson_roadmap(r, modules_spec),
        lesson_paid_info(cid, r, total_h),
    ])

    mod_titles = []
    for i, (name, hours, topics) in enumerate(modules_spec):
        lessons.append(lesson_module(r, i, name, hours, topics))
        mod_titles.append(name)

    learn = list(r.get("learn") or [])
    if not learn:
        learn = [f"Пройти программу {total_h}+ часов", "Выполнить практику по всем модулям", "Сдать итоговый тест"]
    lessons.append(
        {
            "id": f"{cid}-checklist",
            "title": "Итоговый чек-лист программы",
            "type": "practice",
            "duration": f"{max(10, total_h // 50)} ч",
            "checklist": learn + [f"Завершены все {len(modules_spec)} модулей"],
        }
    )

    questions = quiz_from_sheet(rows, cid)
    if questions:
        lessons.append(
            {
                "id": f"{cid}-quiz",
                "title": "Итоговый тест",
                "type": "quiz",
                "duration": "30–45 мин",
                "questions": questions,
            }
        )

    out = {k: v for k, v in r.items() if not str(k).startswith("_")}
    partner = (r.get("partnerUrl") or r.get("url") or "").strip()
    out["partnerUrl"] = partner if partner.startswith("http") else ""
    out["onSite"] = True
    out["lessons"] = lessons
    out["modules"] = mod_titles
    out["totalHours"] = total_h
    out["about"] = clean_about(r.get("desc", ""), r.get("title", ""), r.get("provider", ""))
    out["format"] = r.get("format") or f"Программа {total_h}+ ч · видео + конспект"
    out["contentOnSite"] = True
    out["duration"] = format_duration(r, len(lessons), total_h)
    out["level"] = r.get("level") or ("Продвинутый" if total_h >= 400 else "Средний")
    return out


def write_catalog(data: dict) -> None:
    slim = [{k: v for k, v in r.items() if k != "lessons"} for r in data.get("resources", [])]
    catalog = {"meta": data.get("meta"), "categories": data.get("categories"), "resources": slim}
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    data = json.loads(RES.read_text(encoding="utf-8"))
    if not BACKUP.is_file():
        BACKUP.write_text(RES.read_text(encoding="utf-8"), encoding="utf-8")
    raw_list = data.get("resources", [])
    resources = []
    for i, r in enumerate(raw_list):
        row = dict(r)
        row["_catalog_index"] = i + 1
        resources.append(enrich_resource(row))
        if (i + 1) % 25 == 0 or i == 0:
            print(f"  лонгриды: {i + 1}/{len(raw_list)} …", flush=True)
    data["resources"] = resources
    data.setdefault("meta", {})
    data["meta"]["enriched"] = True
    data["meta"]["lessonPlayer"] = "v7-video-lessons"
    data["meta"]["longreadsFrom"] = 1
    data["meta"]["programHours"] = "300-520"
    RES.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    write_catalog(data)
    avg_lessons = sum(len(r.get("lessons") or []) for r in resources) / len(resources)
    avg_h = sum(r.get("totalHours", 0) for r in resources) / len(resources)
    print(f"OK {len(resources)} programs, avg {avg_lessons:.0f} blocks, avg {avg_h:.0f} h")


if __name__ == "__main__":
    main()
