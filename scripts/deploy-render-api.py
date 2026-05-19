#!/usr/bin/env python3
"""Деплой на Render через API. Положите ключ в Desktop/render-api-key.txt (одна строка rnd_...)."""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

REPO = "https://github.com/kirikov1982evgenii-sketch/hart"
BRANCH = "main"
KEY_FILE = Path.home() / "Desktop" / "render-api-key.txt"

ENV_PAYMENTS = {
    "MARKET_ADMIN_PIN": "YU2i9oLGIT-Te0x7yad-D2RR",
    "MARKET_OWNER_PIN": "mgKDOhSYRw7XSV6liPX5kdK5",
    "MARKET_OWNER_EMAIL": "freelancerwok@mail.ru",
    "MARKET_PAY_SALT": "7F0mGMrqEKxFCaHQAECKnN7cFsDQF8Ch",
    "HART_TELEGRAM_CHAT_ID": "5286191569",
    "HART_SITE_URL": "https://kirikov1982evgenii-sketch.github.io/hart",
    "MARKET_CORS_ORIGINS": "https://kirikov1982evgenii-sketch.github.io/hart",
    "MARKET_SUPPORT_EMAIL": "freelancerwok@mail.ru",
    "MARKET_PAYPAL_EMAIL": "freelancerwok@mail.ru",
    "MARKET_PAY_CARD": "2200702158761978",
    "MARKET_PAY_BANK": "Т-Банк",
    "MARKET_PAY_NAME": "Евгений",
    "MARKET_PRICE_RUB": "199",
    "MARKET_PRICE_USD": "4.99",
    "PYTHON_VERSION": "3.12.0",
}

ENV_BOT = {
    "HART_TELEGRAM_CHAT_ID": "5286191569",
    "HART_SITE_URL": "https://kirikov1982evgenii-sketch.github.io/hart",
    "MARKET_PAYMENT_API": "https://hart-payments.onrender.com",
    "MARKET_SUPPORT_EMAIL": "freelancerwok@mail.ru",
    "MARKET_PAY_CARD": "2200702158761978",
    "MARKET_PAY_BANK": "Т-Банк",
    "MARKET_PAY_NAME": "Евгений",
    "MARKET_PRICE_RUB": "199",
    "MARKET_PRICE_USD": "4.99",
    "PYTHON_VERSION": "3.12.0",
}


def load_token() -> str:
    if not KEY_FILE.is_file():
        print(f"Создайте файл: {KEY_FILE}")
        print("Render → Account Settings → API Keys → Create")
        sys.exit(1)
    return KEY_FILE.read_text(encoding="utf-8").strip()


def load_bot_token() -> str:
    for p in (
        Path(__file__).resolve().parent.parent / ".env.local",
        Path.home() / "Desktop" / "Свободный-Маркет-Интерактив" / ".env.local",
    ):
        if p.is_file():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith("HART_TELEGRAM_BOT_TOKEN="):
                    return line.split("=", 1)[1].strip()
    print("Не найден HART_TELEGRAM_BOT_TOKEN в .env.local")
    sys.exit(1)


def api(method: str, path: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"https://api.render.com/v1{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else {}


def env_list(extra: dict) -> list[dict]:
    return [{"key": k, "value": v} for k, v in extra.items()]


def main() -> None:
    token = load_token()
    bot = load_bot_token()
    ENV_PAYMENTS["HART_TELEGRAM_BOT_TOKEN"] = bot
    ENV_BOT["HART_TELEGRAM_BOT_TOKEN"] = bot

    owner = api("GET", "/owners", token)
    owner_id = owner[0]["owner"]["id"] if isinstance(owner, list) else owner["id"]
    print("Owner:", owner_id)

    for name, env, start, stype in (
        ("hart-payments", ENV_PAYMENTS, "python payment_server.py", "web_service"),
        ("hart-telegram-bot", ENV_BOT, "python telegram_bot.py", "background_worker"),
    ):
        body = {
            "type": stype,
            "name": name,
            "ownerId": owner_id,
            "repo": REPO,
            "branch": BRANCH,
            "autoDeploy": "yes",
            "serviceDetails": {
                "env": "python",
                "envSpecificDetails": {
                    "buildCommand": "pip install -r requirements.txt",
                    "startCommand": start,
                },
                "healthCheckPath": "/api/health" if name == "hart-payments" else None,
            },
            "envVars": env_list(env),
        }
        if body["serviceDetails"]["healthCheckPath"] is None:
            del body["serviceDetails"]["healthCheckPath"]
        try:
            out = api("POST", "/services", token, body)
            print("Created", name, out.get("service", out).get("serviceDetails", {}).get("url", ""))
        except urllib.error.HTTPError as e:
            print(name, e.code, e.read().decode()[:500])


if __name__ == "__main__":
    main()
