"""Оплата через Telegram-бота (связка с payment_server API)."""
from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,253}\.[^@\s]{2,64}$")

# chat_id -> session
SESSIONS: dict[int, dict] = {}

BASE = Path(__file__).resolve().parent
RESOURCES = BASE / "data" / "resources.json"
_courses_cache: dict[str, dict] | None = None


def load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    p = BASE / ".env.local"
    if not p.is_file():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def pay_api_base() -> str:
    import os

    env = load_env()
    return (
        os.getenv("MARKET_PAYMENT_API")
        or env.get("MARKET_PAYMENT_API")
        or "http://127.0.0.1:8766"
    ).rstrip("/")


def pay_get(path: str) -> dict:
    url = pay_api_base() + path
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"ok": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def pay_post(path: str, body: dict) -> dict:
    url = pay_api_base() + path
    raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=raw,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"ok": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def format_card(card: str) -> str:
    d = re.sub(r"\D", "", card or "")
    return re.sub(r"(\d{4})(?=\d)", r"\1 ", d).strip() or d


def course_by_id(course_id: str) -> dict | None:
    global _courses_cache
    if not course_id:
        return None
    if _courses_cache is None:
        _courses_cache = {}
        if RESOURCES.is_file():
            data = json.loads(RESOURCES.read_text(encoding="utf-8"))
            for r in data.get("resources", []):
                rid = r.get("id")
                if rid:
                    _courses_cache[rid] = r
    return _courses_cache.get(course_id)


def session(chat_id: int) -> dict:
    if chat_id not in SESSIONS:
        SESSIONS[chat_id] = {"step": "idle", "region": "ru"}
    return SESSIONS[chat_id]


def reset_session(chat_id: int) -> None:
    SESSIONS.pop(chat_id, None)


def pay_keyboard_region() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "🇷🇺 199 ₽ (карта)", "callback_data": "pay:ru"},
                {"text": "🌍 $4.99 (PayPal)", "callback_data": "pay:intl"},
            ],
            [{"text": "❌ Отмена", "callback_data": "pay:cancel"}],
        ]
    }


def pay_keyboard_main(site: str) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "💳 Оплатить курс", "callback_data": "pay:start"}],
            [{"text": "📋 Мой статус", "callback_data": "pay:status"}],
            [
                {"text": "📚 Каталог", "url": site},
                {"text": "👤 Кабинет", "url": f"{site.rstrip('/')}/cabinet.html"},
            ],
        ]
    }


def register_user(email: str, name: str, telegram_id: int) -> dict:
    return pay_post(
        "/api/user",
        {"email": email, "name": name, "telegram_id": telegram_id},
    )


def pricing(region: str) -> dict:
    data = pay_get(f"/api/pricing?region={region}")
    if data.get("ok"):
        return data
    return {
        "region": region,
        "amount": 199 if region == "ru" else 4.99,
        "currency": "RUB" if region == "ru" else "USD",
        "pay_card": load_env().get("MARKET_PAY_CARD", "2200702158761978"),
        "pay_bank": load_env().get("MARKET_PAY_BANK", "Т-Банк"),
        "pay_name": load_env().get("MARKET_PAY_NAME", "Евгений"),
        "pay_email": load_env().get("MARKET_PAYPAL_EMAIL", ""),
    }


def pay_instructions(s: dict) -> str:
    pr = pricing(s.get("region", "ru"))
    code = s.get("code", "PAY-…")
    email = s.get("email", "")
    course = s.get("course_title") or "выбранный курс"
    lines = [
        "<b>💳 Оплата</b>",
        f"Курс: {course}",
        f"Email: <code>{email}</code>",
        f"Код: <code>{code}</code>",
        "",
    ]
    if pr.get("region") == "ru":
        card = format_card(str(pr.get("pay_card", "")))
        lines += [
            f"Переведите <b>{int(pr['amount'])} ₽</b> на карту:",
            f"<code>{card}</code>",
            f"Банк: {pr.get('pay_bank', 'Т-Банк')}",
            f"Получатель: {pr.get('pay_name', '')}",
            f"В комментарии укажите: <code>{code}</code>",
            "",
            "📎 Отправьте <b>скрин чека</b> следующим сообщением (фото).",
        ]
    else:
        lines += [
            f"Переведите <b>${pr['amount']}</b> на PayPal:",
            f"<code>{pr.get('pay_email', '')}</code>",
            f"В примечании: <code>{code}</code>",
            "",
            "📎 Отправьте скрин перевода (фото).",
        ]
    return "\n".join(lines)


def submit_receipt(s: dict, image_bytes: bytes, mime: str = "image/jpeg") -> dict:
    ext = "png" if mime == "image/png" else "jpg"
    if image_bytes[:4] == b"%PDF":
        ext = "pdf"
        mime = "application/pdf"
    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "email": s["email"],
        "code": s["code"],
        "region": s.get("region", "ru"),
        "course_id": s.get("course_id", ""),
        "course_url": s.get("course_url", ""),
        "course_title": s.get("course_title", "Курс HART"),
        "receipt_b64": f"data:{mime};base64,{b64}",
    }
    return pay_post("/api/claim", payload)


def library_status(email: str, code: str) -> dict:
    q = urllib.parse.urlencode({"email": email, "code": code})
    return pay_get(f"/api/library?{q}")


def parse_start_pay(arg: str) -> str | None:
    """start=pay_COURSE_ID → course id."""
    if not arg:
        return None
    if arg.startswith("pay_"):
        return arg[4:].strip()[:80]
    return None
