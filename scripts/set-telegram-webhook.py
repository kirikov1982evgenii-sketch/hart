#!/usr/bin/env python3
"""Установить webhook Telegram на URL PythonAnywhere (или другой хост)."""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def load_token() -> str:
    for p in (BASE / ".env.local", Path.home() / "Desktop" / "Свободный-Маркет-Интерактив" / ".env.local"):
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("HART_TELEGRAM_BOT_TOKEN="):
                return line.split("=", 1)[1].strip()
    print("Нет HART_TELEGRAM_BOT_TOKEN в .env.local")
    sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование: python scripts/set-telegram-webhook.py https://USER.pythonanywhere.com")
        sys.exit(1)
    base = sys.argv[1].rstrip("/")
    url = base + "/telegram-webhook"
    token = load_token()
    api = f"https://api.telegram.org/bot{token}/setWebhook"
    body = urllib.parse.urlencode({"url": url}).encode()
    req = urllib.request.Request(api, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        print(json.loads(r.read().decode()))
    print("Webhook:", url)


if __name__ == "__main__":
    main()
