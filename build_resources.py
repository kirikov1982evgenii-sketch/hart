#!/usr/bin/env python3
"""Сборка data/resources.json из каталога, премиум-курсов и базовых разделов."""
import json
from datetime import date
from pathlib import Path

from enrich import enrich_premium, enrich_resource

BASE = Path(__file__).resolve().parent
RES = BASE / "data" / "resources.json"
CATALOG = BASE / "data" / "courses_catalog.json"
PREMIUM = BASE / "data" / "premium_courses.json"
LANG_COURSES = BASE / "data" / "programming_languages_courses.json"


def load_json(path: Path, default):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    base = load_json(RES, {"resources": [], "categories": []})
    keep_cats = {"interactive", "methodology"}
    ban = {"Teachers Pay Teachers — Free", "Twinkl (бесплатные)", "Canva for Education", "SlideShare"}
    resources = [r for r in base.get("resources", []) if r["cat"] in keep_cats]
    resources = [r for r in resources if r["title"] not in ban]

    catalog = load_json(CATALOG, {"courses": []}).get("courses", [])
    premium = load_json(PREMIUM, [])
    lang_courses = load_json(LANG_COURSES, [])
    premium_all = premium + lang_courses

    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    def add_course(raw: dict) -> None:
        url = raw.get("url", "").strip().lower()
        title = raw.get("title", "").strip().lower()
        if url in seen_urls or title in seen_titles:
            return
        seen_urls.add(url)
        seen_titles.add(title)
        resources.append(
            {
                "cat": "courses",
                "title": raw["title"],
                "url": raw["url"],
                "desc": raw.get("desc", ""),
                "tags": raw.get("tags", []),
                "free": raw.get("free", True),
            }
        )

    for p in premium_all:
        add_course(p)
    for c in catalog:
        add_course(c)

    used: set[str] = set()
    premium_by_title = {p["title"]: p for p in premium_all}
    enriched = []
    for r in resources:
        if r.get("cat") == "courses" and r["title"] in premium_by_title:
            enriched.append(enrich_premium(premium_by_title[r["title"]], used))
        else:
            enriched.append(enrich_resource(r, used))

    categories = [
        {
            "id": "interactive",
            "name": "Интерактивы к уроку",
            "icon": "🎮",
            "description": "Симуляции, тренажёры, интерактивные задания",
        },
        {
            "id": "methodology",
            "name": "Методические материалы",
            "icon": "📚",
            "description": "Уроки, материалы к экзаменам, методразработки",
        },
        {
            "id": "courses",
            "name": "Курсы и обучение",
            "icon": "🎓",
            "description": "Онлайн-курсы, треки, языки программирования, программы HART",
        },
    ]

    out = {
        "meta": {
            "brand": "Клуб знаний",
            "accent": "HART",
            "title": "Клуб знаний HART",
            "tagline": "Для нас обучение — это искусство",
            "version": "3.1",
            "updated": date.today().isoformat(),
            "total": len(enriched),
            "price": 199,
        },
        "categories": categories,
        "resources": enriched,
    }
    RES.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    n_courses = sum(1 for r in enriched if r["cat"] == "courses")
    print("OK total", len(enriched), "courses", n_courses)


if __name__ == "__main__":
    main()
