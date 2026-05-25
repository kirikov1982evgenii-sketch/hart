#!/usr/bin/env python3
"""Привязать hart-club.ru к GitHub Pages и включить HTTPS (нужен git credential github.com)."""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

OWNER = "kirikov1982evgenii-sketch"
REPO = "hart"
DOMAIN = "hart-club.ru"


def git_token() -> str:
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        timeout=20,
        cwd=Path(__file__).resolve().parent.parent,
    )
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("Нет сохранённого пароля GitHub. Выполните git push — Windows запомнит вход.")


def gh(method: str, path: str, body: dict | None = None) -> dict | list:
    tok = git_token()
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err = e.read().decode(errors="replace")
        raise SystemExit(f"GitHub API {e.code} {path}: {err}") from e


def main() -> int:
    print("Токен из git credential — OK")
    try:
        pages = gh("GET", f"/repos/{OWNER}/{REPO}/pages")
        print("Текущий Pages:", json.dumps(pages, ensure_ascii=False, indent=2))
    except SystemExit as e:
        print(e)
        pages = {}

    print(f"\nПривязка домена {DOMAIN}…")
    gh(
        "PUT",
        f"/repos/{OWNER}/{REPO}/pages",
        {"cname": DOMAIN, "build_type": "workflow"},
    )
    print("Домен сохранён.")

    for i in range(8):
        try:
            health = gh("GET", f"/repos/{OWNER}/{REPO}/pages/health")
            dom = health.get("domain") or health
            print(f"health[{i}]:", json.dumps(dom, ensure_ascii=False))
            if dom.get("is_https_eligible"):
                print("Сертификат готов — включаю Enforce HTTPS…")
                gh(
                    "PUT",
                    f"/repos/{OWNER}/{REPO}/pages",
                    {"cname": DOMAIN, "https_enforced": True, "build_type": "workflow"},
                )
                break
        except SystemExit as e:
            print(e)
        time.sleep(20)
    else:
        print("Сертификат ещё выпускается (до 24 ч). Домен уже привязан — проверьте позже https://hart-club.ru/")

    pages = gh("GET", f"/repos/{OWNER}/{REPO}/pages")
    cert = pages.get("https_certificate") or {}
    print("\nИтог:", pages.get("html_url"), "HTTPS cert:", cert.get("state"), cert.get("domains"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
