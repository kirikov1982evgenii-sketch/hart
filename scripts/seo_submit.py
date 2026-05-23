#!/usr/bin/env python3
"""Пинг sitemap, IndexNow, проверка доступности SEO-файлов."""
from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SITE = os.getenv("HART_SITE_URL", "http://hart-club.ru").rstrip("/")
SITEMAP = f"{SITE}/sitemap.xml"
KEY_FILE = BASE / "indexnow-key.txt"
KEY_TXT = None  # set after load


def load_key() -> str:
    global KEY_TXT
    if KEY_FILE.is_file():
        key = KEY_FILE.read_text(encoding="utf-8").strip()
    else:
        key = str(uuid.uuid4()).replace("-", "")[:32]
        KEY_FILE.write_text(key + "\n", encoding="utf-8")
    KEY_TXT = BASE / f"{key}.txt"
    KEY_TXT.write_text(key, encoding="utf-8")
    return key


def fetch(url: str, method: str = "GET", data: bytes | None = None, headers: dict | None = None) -> tuple[int, str]:
    h = headers or {}
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(500).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read(500).decode("utf-8", errors="replace")
    except Exception as e:
        return 0, str(e)


def ping_sitemaps() -> None:
    pings = [
        ("Bing", f"https://www.bing.com/ping?sitemap={urllib.parse.quote(SITEMAP)}"),
        ("Google (legacy)", f"https://www.google.com/ping?sitemap={urllib.parse.quote(SITEMAP)}"),
    ]
    for name, url in pings:
        code, body = fetch(url)
        print(f"  {name}: HTTP {code} — {body[:120]}")


def indexnow_submit(key: str, urls: list[str]) -> None:
    payload = {
        "host": "hart-club.ru",
        "key": key,
        "keyLocation": f"{SITE}/{key}.txt",
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    for endpoint in (
        "https://api.indexnow.org/IndexNow",
        "https://yandex.com/indexnow",
        "https://www.bing.com/indexnow",
    ):
        code, body = fetch(
            endpoint,
            method="POST",
            data=data,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        print(f"  IndexNow {endpoint.split('/')[2]}: HTTP {code} — {body[:100]}")


def check_files() -> None:
    for path in ("/robots.txt", "/sitemap.xml", f"/{KEY_FILE.read_text().strip()}.txt"):
        code, _ = fetch(SITE + path)
        print(f"  {path}: HTTP {code}")


def main() -> None:
    key = load_key()
    print("IndexNow key:", key, "->", KEY_TXT.name)
    print("Check live files:")
    check_files()
    print("Ping sitemaps:")
    ping_sitemaps()
    urls = [SITE + "/", SITE + "/?lang=en", SITE + "/support.html", SITE + "/pay.html"]
    sm = BASE / "sitemap.xml"
    if sm.is_file():
        import re as _re

        urls = list(dict.fromkeys(_re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8"))))
    else:
        res = json.loads((BASE / "data" / "resources.json").read_text(encoding="utf-8"))
        for r in res.get("resources", []):
            cid = r.get("id")
            if cid:
                urls.append(f"{SITE}/course.html?id={urllib.parse.quote(str(cid))}")
    batch = 500
    for i in range(0, len(urls), batch):
        chunk = urls[i : i + batch]
        print(f"IndexNow batch {i // batch + 1} ({len(chunk)} URLs):")
        indexnow_submit(key, chunk)
    print("Done. Commit", KEY_TXT.name, "and indexnow-key.txt to GitHub.")


if __name__ == "__main__":
    main()
