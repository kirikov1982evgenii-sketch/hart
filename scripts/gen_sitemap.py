#!/usr/bin/env python3
"""Генерация sitemap.xml для Google / Yandex."""
from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RESOURCES = BASE / "data" / "resources.json"
OUT = BASE / "sitemap.xml"

SITE = os.getenv("HART_SITE_URL", "https://hart-club.ru").rstrip("/")
TODAY = date.today().isoformat()

STATIC = [
    ("/", "daily", "1.0"),
    ("/support.html", "monthly", "0.6"),
    ("/pay.html", "monthly", "0.5"),
    ("/courses/poker/index.html", "monthly", "0.4"),
]


def url_elem(parent: ET.Element, loc: str, changefreq: str, priority: str) -> None:
    u = ET.SubElement(parent, "url")
    ET.SubElement(u, "loc").text = loc
    ET.SubElement(u, "lastmod").text = TODAY
    ET.SubElement(u, "changefreq").text = changefreq
    ET.SubElement(u, "priority").text = priority


def main() -> None:
    data = json.loads(RESOURCES.read_text(encoding="utf-8"))
    resources = data.get("resources", [])

    root = ET.Element(
        "urlset",
        xmlns="http://www.sitemaps.org/schemas/sitemap/0.9",
    )

    seen: set[str] = set()
    for path, freq, pri in STATIC:
        loc = f"{SITE}{path}"
        if loc in seen:
            continue
        seen.add(loc)
        url_elem(root, loc, freq, pri)

    for r in resources:
        cid = str(r.get("id", "")).strip()
        if not cid:
            continue
        loc = f"{SITE}/course.html?id={cid}"
        if loc in seen:
            continue
        seen.add(loc)
        url_elem(root, loc, "weekly", "0.7")

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(OUT, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {OUT} — {len(seen)} URLs ({len(resources)} courses)")


if __name__ == "__main__":
    main()
