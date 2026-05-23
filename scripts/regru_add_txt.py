#!/usr/bin/env python3
"""Добавить TXT для Google/Yandex в DNS hart-club.ru через REG.API."""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DOMAIN = "hart-club.ru"
API = "https://api.reg.ru/api/regru2"
TOKEN_FILE = Path.home() / "Desktop" / "regru-api.txt"
CODES_FILE = Path(__file__).resolve().parent.parent / "seo-verification-codes.txt"


def creds() -> tuple[str, str]:
    if not TOKEN_FILE.is_file():
        print(f"Создайте {TOKEN_FILE} (логин + пароль API REG.RU)")
        sys.exit(1)
    lines = [x.strip() for x in TOKEN_FILE.read_text(encoding="utf-8").splitlines() if x.strip() and not x.startswith("#")]
    return lines[0], lines[1]


def call(method: str, user: str, pwd: str, extra: dict) -> dict:
    payload = {"username": user, "password": pwd, **extra}
    body = urllib.parse.urlencode(
        {"input_format": "json", "input_data": json.dumps(payload, ensure_ascii=False)}
    ).encode()
    req = urllib.request.Request(f"{API}/{method}", data=body, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main() -> int:
    if not CODES_FILE.is_file():
        print("Сначала: python scripts/seo_browser_setup.py")
        return 1
    user, pwd = creds()
    for line in CODES_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("GOOGLE_DNS_TXT="):
            txt = line.split("=", 1)[1]
            r = call(
                "zone/add_txt",
                user,
                pwd,
                {"domains": [{"dname": DOMAIN}], "subdomain": "@", "text": txt},
            )
            print("Google TXT:", r.get("result"), r.get("error_text", ""))
        elif line.startswith("YANDEX_META="):
            print("Yandex meta (добавьте в index.html):", line.split("=", 1)[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
