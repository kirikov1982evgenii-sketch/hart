#!/usr/bin/env python3
"""Telegram-бот «Клуб знаний HART» — поддержка, оплата, каталог."""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

import bot_payments as pay

BASE = Path(__file__).resolve().parent


def load_env() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in (BASE / ".env.local",):
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


ENV = load_env()
TOKEN = os.getenv("HART_TELEGRAM_BOT_TOKEN") or ENV.get("HART_TELEGRAM_BOT_TOKEN", "")
SITE = os.getenv("HART_SITE_URL") or ENV.get("HART_SITE_URL", "http://localhost:8765")
SUPPORT = os.getenv("MARKET_SUPPORT_EMAIL") or ENV.get("MARKET_SUPPORT_EMAIL", "freelancerwok@mail.ru")
BOT_USER = ENV.get("HART_TELEGRAM_BOT_USERNAME", "uportbot")


def api(method: str, **params) -> dict:
    if not TOKEN:
        return {}
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def api_json(method: str, payload: dict) -> dict:
    if not TOKEN:
        return {}
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST", headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def send(chat_id: int | str, text: str, reply_markup: dict | None = None) -> None:
    p: dict = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        p["reply_markup"] = json.dumps(reply_markup)
    api("sendMessage", **p)


def answer_callback(callback_id: str, text: str = "") -> None:
    api("answerCallbackQuery", callback_query_id=callback_id, text=text[:200])


def download_file(file_id: str) -> bytes:
    meta = api("getFile", file_id=file_id)
    path = meta.get("result", {}).get("file_path")
    if not path:
        raise ValueError("file_path missing")
    url = f"https://api.telegram.org/file/bot{TOKEN}/{path}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def keyboard() -> dict:
    return pay.pay_keyboard_main(SITE)


def start_pay_flow(chat_id: int, course_id: str | None = None) -> None:
    s = pay.session(chat_id)
    s["step"] = "region"
    s["course_id"] = course_id or ""
    c = pay.course_by_id(course_id) if course_id else None
    if c:
        s["course_title"] = c.get("title", "")
        s["course_url"] = c.get("url", "")
    else:
        s["course_title"] = ""
        s["course_url"] = ""
    title = s.get("course_title") or "курс из каталога"
    send(
        chat_id,
        f"<b>Оплата:</b> {title}\n\nВыберите регион оплаты:",
        pay.pay_keyboard_region(),
    )


def handle_pay_callback(chat_id: int, data: str, callback_id: str = "") -> None:
    action = data.split(":", 1)[1] if ":" in data else ""
    s = pay.session(chat_id)

    def ack(text: str = "") -> None:
        if callback_id:
            answer_callback(callback_id, text)

    if action == "cancel":
        pay.reset_session(chat_id)
        ack("Отменено")
        send(chat_id, "Оплата отменена.", keyboard())
        return

    if action == "start":
        ack()
        start_pay_flow(chat_id)
        return

    if action == "status":
        ack()
        if not s.get("email") or not s.get("code"):
            send(
                chat_id,
                "Сначала начните оплату: /pay и укажите email.",
                keyboard(),
            )
            return
        lib = pay.library_status(s["email"], s["code"])
        if not lib.get("ok"):
            send(chat_id, f"Не удалось проверить: {lib.get('error', 'ошибка')}", keyboard())
            return
        courses = lib.get("courses") or []
        if courses:
            lines = ["<b>Ваши оплаченные курсы:</b>"]
            for c in courses[:15]:
                lines.append(f"• {c.get('title', 'Курс')}")
            send(chat_id, "\n".join(lines), keyboard())
        else:
            send(
                chat_id,
                "Пока нет подтверждённых курсов. Если отправили чек — ждём проверки (до 24 ч).",
                keyboard(),
            )
        return

    if action in ("ru", "intl"):
        s["step"] = "email"
        s["region"] = action
        ack()
        send(
            chat_id,
            "Введите <b>email</b> — на него привяжем оплату и личный кабинет на сайте:",
        )
        return

    ack()


def handle_email_step(chat_id: int, text: str) -> bool:
    s = pay.session(chat_id)
    if s.get("step") != "email":
        return False
    email = text.strip().lower()
    if not pay.EMAIL_RE.match(email):
        send(chat_id, "Некорректный email. Пример: <code>you@mail.ru</code>")
        return True
    reg = pay.register_user(email, "", chat_id)
    if not reg.get("ok"):
        send(chat_id, f"Ошибка: {reg.get('error', 'сервер оплат недоступен')}\nЗапустите start-site.bat")
        return True
    s["email"] = email
    s["code"] = reg["code"]
    s["step"] = "receipt"
    send(chat_id, pay.pay_instructions(s))
    return True


def handle_receipt_photo(chat_id: int, msg: dict) -> bool:
    s = pay.session(chat_id)
    if s.get("step") != "receipt":
        return False
    if not s.get("email") or not s.get("code"):
        send(chat_id, "Сначала /pay и укажите email.")
        return True

    photo = msg.get("photo")
    doc = msg.get("document")
    file_id = None
    mime = "image/jpeg"
    if photo:
        file_id = photo[-1]["file_id"]
    elif doc:
        mime = doc.get("mime_type") or "application/octet-stream"
        if not mime.startswith("image/") and mime != "application/pdf":
            send(chat_id, "Пришлите фото чека или PDF.")
            return True
        file_id = doc["file_id"]
    else:
        return False

    try:
        raw = download_file(file_id)
    except Exception as e:
        send(chat_id, f"Не удалось загрузить файл: {e}")
        return True

    res = pay.submit_receipt(s, raw, mime)
    if not res.get("ok"):
        send(chat_id, f"❌ {res.get('error', 'Ошибка отправки чека')}")
        return True

    s["step"] = "done"
    send(
        chat_id,
        "✅ <b>Чек принят!</b>\n\n"
        f"Заявка <code>{res.get('claim_id', '')}</code> на проверке.\n"
        "Обычно до 24 часов. Статус: /status или кнопка «Мой статус».\n"
        f"Кабинет: {SITE.rstrip('/')}/cabinet.html",
        keyboard(),
    )
    return True


def handle_message(msg: dict) -> None:
    chat_id = msg["chat"]["id"]
    text = (msg.get("text") or "").strip()

    if handle_receipt_photo(chat_id, msg):
        return

    if text.startswith("/start"):
        pay.reset_session(chat_id)
        arg = text.split(maxsplit=1)[1] if " " in text else ""
        course_id = pay.parse_start_pay(arg)
        send(
            chat_id,
            f"<b>Клуб знаний HART</b>\n\n"
            f"Онлайн-курсы с личным кабинетом.\n"
            f"🇷🇺 СНГ — 199 ₽ · 🌍 Европа/США — $4.99\n\n"
            f"💳 Оплатить можно здесь в боте — кнопка ниже.\n"
            f"Сайт: {SITE}\n"
            f"Почта: {SUPPORT}",
            keyboard(),
        )
        if course_id:
            start_pay_flow(chat_id, course_id)
        return

    if text.startswith("/pay") or text.lower() in ("оплата", "оплатить", "купить"):
        parts = text.split(maxsplit=1)
        cid = parts[1].strip() if len(parts) > 1 else None
        start_pay_flow(chat_id, cid)
        return

    if text.startswith("/status"):
        handle_pay_callback(chat_id, "pay:status")
        return

    if handle_email_step(chat_id, text):
        return

    if text.startswith("/help") or text.startswith("/support"):
        send(
            chat_id,
            f"<b>Поддержка</b>\n"
            f"✉️ <a href='mailto:{SUPPORT}'>{SUPPORT}</a>\n"
            f"🌐 <a href='{SITE}/support.html'>Страница поддержки</a>\n\n"
            f"<b>Оплата в боте:</b> /pay → email → перевод → фото чека",
            keyboard(),
        )
        return

    if text.startswith("/catalog"):
        send(chat_id, f"Каталог курсов:\n{SITE}", keyboard())
        return

    if text.startswith("/cabinet"):
        send(chat_id, f"Личный кабинет:\n{SITE.rstrip('/')}/cabinet.html", keyboard())
        return

    send(
        chat_id,
        "Команды:\n"
        "/start — меню\n"
        "/pay — оплатить курс в боте\n"
        "/status — статус оплаты\n"
        "/catalog — каталог\n"
        "/cabinet — кабинет\n"
        "/support — помощь",
        keyboard(),
    )


def handle_callback(query: dict) -> None:
    data = query.get("data") or ""
    chat_id = query["message"]["chat"]["id"]
    callback_id = query["id"]
    if data.startswith("pay:"):
        handle_pay_callback(chat_id, data, callback_id)
        return
    answer_callback(callback_id)


def process_update(update: dict) -> None:
    """Одно обновление (webhook или polling)."""
    if "callback_query" in update:
        handle_callback(update["callback_query"])
    elif "message" in update:
        handle_message(update["message"])


def poll() -> None:
    if not TOKEN:
        print("[!] Задайте HART_TELEGRAM_BOT_TOKEN в .env.local", flush=True)
        print(f"  BotFather → создайте бота → username: {BOT_USER}", flush=True)
        return
    print(f"HART Telegram bot @{BOT_USER} polling…", flush=True)
    print(f"  Payment API: {pay.pay_api_base()}", flush=True)
    offset = 0
    while True:
        try:
            data = api("getUpdates", timeout=50, offset=offset)
            for u in data.get("result", []):
                offset = u["update_id"] + 1
                process_update(u)
        except Exception as e:
            print("poll error:", e, flush=True)
            time.sleep(5)


if __name__ == "__main__":
    poll()
