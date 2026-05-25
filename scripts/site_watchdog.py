#!/usr/bin/env python3
"""Проверка hart-club.ru и локального каталога; автоисправление HTTPS."""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROD = "https://hart-club.ru"
LOCAL = "http://127.0.0.1:8765"


def fetch(url: str, timeout: int = 45) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "HART-Watchdog/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def check_url(base: str) -> list[str]:
    issues = []
    for path in ("/", "/data/resources.json", "/data/i18n.json"):
        url = base.rstrip("/") + path
        try:
            code, body = fetch(url)
            if code != 200:
                issues.append(f"{url} HTTP {code}")
            elif path.endswith(".json"):
                json.loads(body.decode("utf-8"))
        except urllib.error.URLError as e:
            issues.append(f"{url} — {e.reason}")
        except json.JSONDecodeError:
            issues.append(f"{url} — невалидный JSON")
    return issues


def fix_https() -> bool:
    script = ROOT / "scripts" / "fix-pages-https.py"
    if not script.is_file():
        return False
    print("Исправление HTTPS через GitHub API…")
    r = subprocess.run([sys.executable, str(script)], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout[-800:] if r.stdout else "")
    if r.returncode != 0:
        print(r.stderr[-400:] if r.stderr else "")
    return r.returncode == 0


def main() -> int:
    print("=== HART site watchdog ===\n")
    prod_issues = check_url(PROD)
    if prod_issues:
        print("Продакшен:", *prod_issues, sep="\n  ")
        if any("SSL" in x or "certificate" in x.lower() for x in prod_issues):
            fix_https()
            prod_issues = check_url(PROD)
    else:
        print("Продакшен OK:", PROD)

    local_issues = check_url(LOCAL)
    if local_issues:
        print("Локально (запустите start-site.bat):", *local_issues, sep="\n  ")
    else:
        print("Локально OK:", LOCAL)

    qa = subprocess.run([sys.executable, str(ROOT / "scripts" / "qa_audit.py")], cwd=ROOT)
    if qa.returncode:
        print("QA: есть замечания (см. выше)")
    else:
        print("QA: каталог курсов в норме")

    if prod_issues:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
