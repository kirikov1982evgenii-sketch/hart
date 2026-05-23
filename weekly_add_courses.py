#!/usr/bin/env python3
"""Каждую неделю добавляет 2–3 курса из очереди и пересобирает каталог."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
CATALOG = BASE / "data" / "courses_catalog.json"
QUEUE = BASE / "data" / "weekly_queue.json"
STATE = BASE / "data" / "weekly_state.json"
MIN_ADD = 2
MAX_ADD = 3
DAYS_BETWEEN = 7


def load_json(path: Path, default):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def catalog_keys(catalog: list[dict]) -> set[str]:
    keys = set()
    for c in catalog:
        keys.add(c.get("url", "").strip().lower())
        keys.add(c.get("title", "").strip().lower())
    return keys


def main() -> int:
    force = "--force" in sys.argv
    state = load_json(STATE, {"last_run": None, "history": []})
    last = state.get("last_run")
    now = datetime.now(timezone.utc)

    if last and not force:
        try:
            prev = datetime.fromisoformat(last.replace("Z", "+00:00"))
            if (now - prev).days < DAYS_BETWEEN:
                print(f"Пропуск: прошло {(now - prev).days} дн., нужно {DAYS_BETWEEN}")
                return 0
        except ValueError:
            pass

    catalog_data = load_json(CATALOG, {"courses": []})
    catalog: list[dict] = catalog_data.get("courses", [])
    existing = catalog_keys(catalog)

    queue_data = load_json(QUEUE, {"courses": []})
    queue: list[dict] = queue_data.get("courses", [])

    added: list[dict] = []
    for item in queue:
        if len(added) >= MAX_ADD:
            break
        url = item.get("url", "").strip().lower()
        title = item.get("title", "").strip().lower()
        if url in existing or title in existing:
            continue
        entry = {
            "cat": "courses",
            "title": item["title"],
            "url": item["url"],
            "desc": item.get("desc", ""),
            "tags": item.get("tags", []),
            "free": True,
            "added_at": now.isoformat(),
            "source": "weekly_auto",
        }
        catalog.append(entry)
        existing.add(url)
        existing.add(title)
        added.append({"title": item["title"], "url": item["url"]})

    if len(added) < MIN_ADD:
        print(f"В очереди мало новых курсов (добавлено {len(added)}). Пополните data/weekly_queue.json")
        if not added:
            return 1

    catalog_data["courses"] = catalog
    save_json(CATALOG, catalog_data)

    state["last_run"] = now.isoformat()
    state.setdefault("history", []).append(
        {"date": now.isoformat(), "added": added, "count": len(added)}
    )
    state["history"] = state["history"][-52:]
    save_json(STATE, state)

    print(f"Добавлено курсов: {len(added)}")
    for a in added:
        print(" +", a["title"])

    subprocess.run([sys.executable, str(BASE / "build_resources.py")], check=True, cwd=BASE)
    print("Каталог пересобран: data/resources.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
