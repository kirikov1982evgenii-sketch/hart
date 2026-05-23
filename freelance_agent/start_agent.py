#!/usr/bin/env python3
"""
Агент фриланса: FL.ru + весь мир, общение с заказчиками, предоплата Т-Банк.
Работает через @workmy1bot (токен из курсор/fl-orders-bot/.env).

Не запускайте одновременно telegram_bot.py (HART @uportbot) — конфликт 409.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

MARKET = Path(__file__).resolve().parent.parent
FL_BOT = Path(__file__).resolve().parent.parent.parent / "курсор" / "fl-orders-bot"
if not FL_BOT.is_dir():
    FL_BOT = Path(r"c:\Users\Falcoone\Desktop\курсор\fl-orders-bot")

BOT_USERNAME = "workmy1bot"


def load_kv(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def apply_env() -> None:
    local = load_kv(MARKET / ".env.local")
    fl_env = load_kv(FL_BOT / ".env")

    # @workmy1bot — из fl-orders-bot/.env (приоритет)
    token = fl_env.get("TELEGRAM_BOT_TOKEN", "")
    chat = fl_env.get("TELEGRAM_CHAT_ID", "")
    if token:
        os.environ["TELEGRAM_BOT_TOKEN"] = token
    if chat:
        os.environ["TELEGRAM_CHAT_ID"] = chat

    os.environ["TELEGRAM_BOT_USERNAME"] = fl_env.get("TELEGRAM_BOT_USERNAME", BOT_USERNAME).lstrip("@")
    os.environ["HART_TELEGRAM_BOT_USERNAME"] = os.environ["TELEGRAM_BOT_USERNAME"]

    os.environ.setdefault("CURSOR_AGENT", "1")
    os.environ.setdefault("WORLD_JOBS", "1")
    os.environ.setdefault("FULL_AUTO", "1")
    os.environ.setdefault("AUTONOMOUS_ONLY", "1")
    os.environ.setdefault("AUTO_REPLY", "1")
    os.environ.setdefault("AUTO_REPLY_PAYMENT", "1")
    os.environ.setdefault("AUTO_APPLY", "1")
    os.environ.setdefault("AUTO_EXECUTE", "1")
    os.environ.setdefault("AI_SOLO", "1")
    os.environ.setdefault("INBOX_POLL_INTERVAL", "60")
    os.environ.setdefault("FOLLOWUP_INTERVAL", "300")

    os.environ["PAYMENT_BANK"] = local.get("MARKET_PAY_BANK") or fl_env.get("PAYMENT_BANK", "Т-Банк")
    os.environ["PAYMENT_NAME"] = local.get("MARKET_PAY_NAME") or fl_env.get("PAYMENT_NAME", "Евгений")
    os.environ["PAYMENT_CARD"] = local.get("MARKET_PAY_CARD") or fl_env.get("PAYMENT_CARD", "2200702158761978")
    if not os.environ.get("PAYMENT_PHONE"):
        os.environ["PAYMENT_PHONE"] = fl_env.get("PAYMENT_PHONE", "")


def main() -> int:
    if not FL_BOT.is_dir():
        print("Не найден fl-orders-bot:", FL_BOT, file=sys.stderr)
        return 1
    apply_env()
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        print("Нет TELEGRAM_BOT_TOKEN в курсор/fl-orders-bot/.env", file=sys.stderr)
        return 1

    sys.path.insert(0, str(FL_BOT))
    os.chdir(FL_BOT)

    from run_bot_service import main as run_main

    uname = os.environ.get("TELEGRAM_BOT_USERNAME", BOT_USERNAME)
    print(f"Freelance agent -> @{uname} | FL.ru + world | Cursor filter ON", flush=True)
    return run_main()


if __name__ == "__main__":
    raise SystemExit(main())
