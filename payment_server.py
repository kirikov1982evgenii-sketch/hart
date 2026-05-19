#!/usr/bin/env python3
"""API оплат: лимиты, CORS, проверка чеков, PIN только с сервера."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from security_common import (
    API_CSP,
    CLAIM_ID_RE,
    EMAIL_RE,
    PinGuard,
    admin_pin,
    apply_cors,
    apply_security_headers,
    client_ip,
    decode_receipt_b64,
    detect_receipt_ext,
    is_safe_http_url,
    load_env_local,
    pin_guard,
    rate_limit_or_429,
    read_json_body,
    rl_access,
    rl_admin,
    rl_claim,
    rl_claim_email,
    rl_code,
    rl_user,
)
from server_common import bind_host, service_port

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
CLAIMS_FILE = DATA / "payment_claims.json"
USERS_FILE = DATA / "users.json"
RECEIPTS = DATA / "receipts"

load_env_local()
PORT = service_port("PAYMENT_API_PORT", 8766)
HOST = bind_host()
SALT = os.getenv("MARKET_PAY_SALT", "market-pay-salt-v1")
ADMIN_PIN = admin_pin()
OWNER_EMAIL = os.getenv("MARKET_OWNER_EMAIL", "freelancerwok@mail.ru").lower().strip()
OWNER_PIN = os.getenv("MARKET_OWNER_PIN", ADMIN_PIN)
PAYPAL_EMAIL = os.getenv("MARKET_PAYPAL_EMAIL", "freelancerwok@mail.ru")
PRICE_RUB = float(os.getenv("MARKET_PRICE_RUB", "199"))
PRICE_USD = float(os.getenv("MARKET_PRICE_USD", "4.99"))


def load_dotenv(path: Path) -> dict[str, str]:
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


def site_env() -> dict[str, str]:
    env = load_dotenv(BASE / ".env.local")
    if not env.get("HART_TELEGRAM_BOT_TOKEN"):
        for p in (
            BASE.parent / "курсор" / "fl-orders-bot" / ".env",
            Path(r"c:\Users\Falcoone\Desktop\курсор\fl-orders-bot\.env"),
        ):
            env = {**load_dotenv(p), **env}
    return env


def tg_config() -> tuple[str, str]:
    env = site_env()
    token = env.get("HART_TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_BOT_TOKEN", "")
    chat = env.get("HART_TELEGRAM_CHAT_ID") or env.get("TELEGRAM_CHAT_ID", "")
    return token, chat


def pricing_for_region(region: str) -> dict:
    if region == "ru":
        return {
            "region": "ru",
            "amount": PRICE_RUB,
            "currency": "RUB",
            "pay_method": "card",
            "pay_card": os.getenv("MARKET_PAY_CARD", "2200702158761978"),
            "pay_bank": os.getenv("MARKET_PAY_BANK", "Т-Банк"),
            "pay_name": os.getenv("MARKET_PAY_NAME", "Евгений"),
        }
    return {
        "region": "intl",
        "amount": PRICE_USD,
        "currency": "USD",
        "pay_method": "paypal",
        "pay_email": PAYPAL_EMAIL,
    }


def check_owner(email: str, pin: str) -> bool:
    if email.lower().strip() != OWNER_EMAIL:
        return False
    return pin_guard.check("owner", pin, OWNER_PIN)


def payment_code(email: str) -> str:
    h = hashlib.sha256(f"{SALT}:{email.lower().strip()}".encode()).hexdigest()[:8].upper()
    return f"PAY-{h}"


def load_claims() -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    if not CLAIMS_FILE.is_file():
        return {"claims": [], "approved_emails": []}
    return json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))


def save_claims(data: dict) -> None:
    CLAIMS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_users() -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.is_file():
        return {"users": {}}
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def save_users(data: dict) -> None:
    USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_user(email: str, name: str = "", telegram_id: int | None = None) -> dict:
    store = load_users()
    em = email.lower().strip()
    users = store.setdefault("users", {})
    if em not in users:
        users[em] = {
            "email": em,
            "name": name[:80] if name else "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "courses": [],
        }
        if telegram_id:
            users[em]["telegram_id"] = int(telegram_id)
        save_users(store)
    else:
        changed = False
        if name and not users[em].get("name"):
            users[em]["name"] = name[:80]
            changed = True
        if telegram_id:
            users[em]["telegram_id"] = int(telegram_id)
            changed = True
        if changed:
            save_users(store)
    return users[em]


def add_course_to_library(email: str, course: dict) -> None:
    em = email.lower().strip()
    ensure_user(em)
    store = load_users()
    users = store.setdefault("users", {})
    user = users[em]
    cid = str(course.get("course_id", ""))[:80]
    existing = {c.get("course_id") for c in user.get("courses", [])}
    if cid and cid in existing:
        return
    entry = {
        "course_id": cid,
        "title": str(course.get("title", ""))[:200],
        "url": str(course.get("url", ""))[:500],
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }
    user.setdefault("courses", []).append(entry)
    save_users(store)


def user_library(email: str) -> list[dict]:
    em = email.lower().strip()
    store = load_users()
    user = store.get("users", {}).get(em)
    if user:
        return list(user.get("courses", []))
    return []


def has_course_access(email: str, course_id: str) -> bool:
    em = email.lower().strip()
    cid = (course_id or "").strip().lower()
    if not cid:
        return False
    for c in user_library(em):
        if (c.get("course_id") or "").lower() == cid:
            return True
    data = load_claims()
    for c in data.get("claims", []):
        if (
            c.get("email", "").lower() == em
            and c.get("status") == "approved"
            and (c.get("course_id") or "").lower() == cid
        ):
            return True
    return False


def auth_email_code(email: str, code: str) -> bool:
    if not EMAIL_RE.match(email):
        return False
    return payment_code(email) == code.upper()


def tg_send(text: str, chat_id: str | int | None = None) -> None:
    token, admin_chat = tg_config()
    if not token:
        return
    target = chat_id if chat_id is not None else admin_chat
    if not target:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode(
        {
            "chat_id": target,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode()
    try:
        urllib.request.urlopen(
            urllib.request.Request(url, data=body, method="POST"), timeout=15
        )
    except Exception:
        pass


def tg_notify_user(email: str, text: str) -> None:
    em = email.lower().strip()
    user = load_users().get("users", {}).get(em)
    tid = user.get("telegram_id") if user else None
    if tid:
        tg_send(text, tid)


def check_admin(handler, pin: str) -> bool:
    ip = client_ip(handler)
    if pin_guard.locked(ip):
        return False
    return pin_guard.check(ip, pin, ADMIN_PIN)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _json(self, code: int, obj: dict):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        apply_cors(self)
        apply_security_headers(self, csp=API_CSP)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        apply_cors(self)
        apply_security_headers(self, csp=API_CSP)
        self.end_headers()

    def do_GET(self):
        ip = client_ip(self)
        parsed = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/api/code":
            if not rate_limit_or_429(self, rl_code, ip):
                return
            email = (q.get("email") or [""])[0].strip().lower()[:254]
            if not EMAIL_RE.match(email):
                return self._json(400, {"ok": False, "error": "Некорректный email"})
            ensure_user(email)
            region = (q.get("region") or ["intl"])[0][:8]
            if region not in ("ru", "intl"):
                region = "intl"
            return self._json(
                200,
                {
                    "ok": True,
                    "code": payment_code(email),
                    "courses_count": len(user_library(email)),
                    "pricing": pricing_for_region(region),
                },
            )

        if parsed.path in ("/api/health", "/health"):
            return self._json(200, {"ok": True, "service": "hart-payments"})

        if parsed.path == "/api/pricing":
            region = (q.get("region") or ["intl"])[0][:8]
            if region not in ("ru", "intl"):
                region = "intl"
            return self._json(200, {"ok": True, **pricing_for_region(region)})

        if parsed.path == "/api/owner/dashboard":
            if not rate_limit_or_429(self, rl_admin, ip):
                return
            em = (q.get("email") or [""])[0].strip().lower()[:254]
            pin = self.headers.get("X-Owner-Pin", "") or (q.get("pin") or [""])[0]
            if not check_owner(em, pin):
                return self._json(403, {"ok": False, "error": "Доступ только для владельца"})
            users = load_users().get("users", {})
            claims = load_claims().get("claims", [])
            pending = [c for c in claims if c.get("status") == "pending"]
            approved = [c for c in claims if c.get("status") == "approved"]
            return self._json(
                200,
                {
                    "ok": True,
                    "email": OWNER_EMAIL,
                    "users_count": len(users),
                    "pending": pending,
                    "approved_count": len(approved),
                    "telegram": site_env().get("HART_TELEGRAM_BOT_USERNAME", ""),
                },
            )

        if parsed.path == "/api/library":
            if not rate_limit_or_429(self, rl_access, ip):
                return
            email = (q.get("email") or [""])[0].strip().lower()[:254]
            code = (q.get("code") or [""])[0].strip().upper()[:20]
            if not auth_email_code(email, code):
                return self._json(403, {"ok": False, "error": "Неверный код доступа"})
            user = ensure_user(email)
            return self._json(
                200,
                {
                    "ok": True,
                    "user": {"email": email, "name": user.get("name", "")},
                    "courses": user_library(email),
                },
            )

        if parsed.path == "/api/access":
            if not rate_limit_or_429(self, rl_access, ip):
                return
            email = (q.get("email") or [""])[0].strip().lower()[:254]
            code = (q.get("code") or [""])[0].strip().upper()[:20]
            course_id = (q.get("course_id") or [""])[0].strip()[:80]
            if not auth_email_code(email, code):
                return self._json(403, {"ok": False, "approved": False})
            approved = has_course_access(email, course_id) if course_id else False
            return self._json(200, {"ok": True, "approved": approved})

        if parsed.path == "/api/pending":
            if not rate_limit_or_429(self, rl_admin, ip):
                return
            pin = self.headers.get("X-Admin-Pin", "")
            if not check_admin(self, pin):
                return self._json(
                    403,
                    {
                        "ok": False,
                        "error": "Неверный PIN или временная блокировка",
                    },
                )
            pending = [
                c
                for c in load_claims().get("claims", [])
                if c.get("status") == "pending"
            ]
            return self._json(200, {"ok": True, "claims": pending})

        self._json(404, {"ok": False})

    def do_POST(self):
        ip = client_ip(self)
        parsed = urllib.parse.urlparse(self.path)
        data = read_json_body(self)
        if data is None:
            return self._json(400, {"ok": False, "error": "Некорректный запрос"})

        if parsed.path == "/api/claim":
            if not rate_limit_or_429(self, rl_claim, ip):
                return
            email = str(data.get("email", "")).strip().lower()[:254]
            if not EMAIL_RE.match(email):
                return self._json(400, {"ok": False, "error": "Укажите реальный email"})
            if not rate_limit_or_429(self, rl_claim_email, email):
                return self._json(429, {"ok": False, "error": "Лимит заявок с этого email"})
            code = payment_code(email)
            if str(data.get("code", "")).upper() != code:
                return self._json(400, {"ok": False, "error": "Неверный код оплаты"})
            course_url = str(data.get("course_url", ""))[:500]
            if course_url and not is_safe_http_url(course_url):
                return self._json(400, {"ok": False, "error": "Некорректная ссылка на курс"})
            raw = decode_receipt_b64(str(data.get("receipt_b64", "")))
            if raw is None:
                return self._json(
                    400,
                    {"ok": False, "error": "Прикрепите скрин чека (JPG, PNG, PDF или WebP)"},
                )
            ext = detect_receipt_ext(raw)
            store = load_claims()
            tid = data.get("telegram_id")
            tg_id = int(tid) if tid is not None and str(tid).isdigit() else None
            ensure_user(email, str(data.get("name", ""))[:80], telegram_id=tg_id)
            region = str(data.get("region", "intl"))[:8]
            if region not in ("ru", "intl"):
                region = "intl"
            pr = pricing_for_region(region)
            claim = {
                "id": secrets.token_hex(6),
                "email": email,
                "code": code,
                "course_id": str(data.get("course_id", ""))[:80],
                "course_url": course_url,
                "course_title": str(data.get("course_title", ""))[:200],
                "region": region,
                "amount": pr["amount"],
                "currency": pr["currency"],
                "status": "pending",
                "has_receipt": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            RECEIPTS.mkdir(parents=True, exist_ok=True)
            fp = RECEIPTS / f"{claim['id']}.{ext}"
            fp.write_bytes(raw)
            claim["receipt_file"] = fp.name
            store["claims"] = [
                c
                for c in store.get("claims", [])
                if c.get("email") != email or c.get("status") != "pending"
            ]
            store["claims"].append(claim)
            save_claims(store)
            tg_send(
                f"💳 Заявка {claim['amount']} {claim['currency']}\n"
                f"Email: {email}\n"
                f"Код: {code}\n"
                f"Курс: {claim['course_title'][:80]}\n"
                f"Регион: {region}\n"
                f"ID: {claim['id']}"
            )
            return self._json(200, {"ok": True, "claim_id": claim["id"], "status": "pending"})

        if parsed.path in ("/api/approve", "/api/reject"):
            if not rate_limit_or_429(self, rl_admin, ip):
                return
            pin = self.headers.get("X-Admin-Pin", "")
            if not check_admin(self, pin):
                return self._json(
                    403,
                    {
                        "ok": False,
                        "error": "Неверный PIN или временная блокировка",
                    },
                )

        if parsed.path == "/api/approve":
            cid = str(data.get("claim_id", ""))[:32]
            code = str(data.get("code", "")).upper()[:20]
            if cid and not CLAIM_ID_RE.match(cid):
                return self._json(400, {"ok": False, "error": "Некорректный ID"})
            store = load_claims()
            found = None
            for c in store.get("claims", []):
                if cid and c.get("id") == cid:
                    found = c
                    break
                if code and c.get("code") == code and c.get("status") == "pending":
                    found = c
                    break
            if not found:
                return self._json(404, {"ok": False, "error": "Заявка не найдена"})
            found["status"] = "approved"
            found["approved_at"] = datetime.now(timezone.utc).isoformat()
            save_claims(store)
            add_course_to_library(
                found["email"],
                {
                    "course_id": found.get("course_id", ""),
                    "title": found.get("course_title", ""),
                    "url": found.get("course_url", ""),
                },
            )
            tg_send(
                f"✅ Оплата подтверждена\n{found['email']}\n"
                f"{found.get('course_title', '')[:60]}"
            )
            tg_notify_user(
                found["email"],
                f"✅ Оплата подтверждена!\n"
                f"Курс: {found.get('course_title', 'доступ')[:80]}\n"
                f"Кабинет: {site_env().get('HART_SITE_URL', 'http://localhost:8765').rstrip('/')}/cabinet.html",
            )
            return self._json(200, {"ok": True, "email": found["email"]})

        if parsed.path == "/api/user":
            if not rate_limit_or_429(self, rl_user, ip):
                return
            email = str(data.get("email", "")).strip().lower()[:254]
            if not EMAIL_RE.match(email):
                return self._json(400, {"ok": False, "error": "Некорректный email"})
            name = str(data.get("name", ""))[:80]
            tid = data.get("telegram_id")
            tg_id = int(tid) if tid is not None and str(tid).isdigit() else None
            user = ensure_user(email, name, telegram_id=tg_id)
            return self._json(
                200,
                {
                    "ok": True,
                    "code": payment_code(email),
                    "user": {"email": email, "name": user.get("name", "")},
                },
            )

        if parsed.path == "/api/reject":
            cid = str(data.get("claim_id", ""))[:32]
            if not CLAIM_ID_RE.match(cid):
                return self._json(400, {"ok": False, "error": "Некорректный ID"})
            store = load_claims()
            for c in store.get("claims", []):
                if c.get("id") == cid:
                    c["status"] = "rejected"
                    save_claims(store)
                    tg_send(f"❌ Заявка отклонена {c.get('email')} {c.get('code')}")
                    return self._json(200, {"ok": True})
            return self._json(404, {"ok": False})

        self._json(404, {"ok": False})


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    if ADMIN_PIN == "199-admin-change-me":
        print(
            "[!] Смените MARKET_ADMIN_PIN в .env.local (сейчас слабый PIN по умолчанию)",
            flush=True,
        )
    print(f"Payment API http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
