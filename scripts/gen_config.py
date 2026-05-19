#!/usr/bin/env python3
"""Генерация config.js из переменных окружения (Cloudflare Pages / Render build)."""
from __future__ import annotations

import json
import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "config.js"
EXAMPLE = BASE / "config.example.js"


def env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def main() -> None:
    site = env("HART_SITE_URL", "http://localhost:8765").rstrip("/")
    api = env("MARKET_PAYMENT_API", "http://127.0.0.1:8766").rstrip("/")
    bot = env("HART_TELEGRAM_BOT_USERNAME", "uportbot").lstrip("@")

    cfg = {
        "brand": env("HART_BRAND", "Клуб знаний"),
        "accent": env("HART_ACCENT", "HART"),
        "tagline": env("HART_TAGLINE", "Для нас обучение — это искусство"),
        "priceRub": float(env("MARKET_PRICE_RUB", "199")),
        "priceUsd": float(env("MARKET_PRICE_USD", "4.99")),
        "payBank": env("MARKET_PAY_BANK", "Т-Банк"),
        "payCard": env("MARKET_PAY_CARD", "2200702158761978"),
        "payName": env("MARKET_PAY_NAME", "Евгений"),
        "payPalEmail": env("MARKET_PAYPAL_EMAIL", "freelancerwok@mail.ru"),
        "paymentApiUrl": api,
        "siteUrl": site,
        "supportEmail": env("MARKET_SUPPORT_EMAIL", "freelancerwok@mail.ru"),
        "ownerEmail": env("MARKET_OWNER_EMAIL", "freelancerwok@mail.ru"),
        "telegramBot": f"https://t.me/{bot}",
        "telegramBotName": bot,
    }

    lines = ["window.SITE_CONFIG = " + json.dumps(cfg, ensure_ascii=False, indent=2) + ";", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote", OUT)
    print("  siteUrl:", site)
    print("  paymentApiUrl:", api)


if __name__ == "__main__":
    main()
