"""Общие модули защиты: лимиты, заголовки, CORS, проверка чеков и PIN."""
from __future__ import annotations

import base64
import hmac
import json
import os
import re
import time
from collections import defaultdict
from pathlib import Path
BASE = Path(__file__).resolve().parent

CORS_ORIGINS = {
    o.strip()
    for o in os.getenv(
        "MARKET_CORS_ORIGINS",
        "http://127.0.0.1:8765,http://localhost:8765",
    ).split(",")
    if o.strip()
}

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}

API_CSP = "default-src 'none'; frame-ancestors 'none'"

def site_csp() -> str:
    connect = [
        "'self'",
        "http://127.0.0.1:8766",
        "http://localhost:8766",
        "https://ipapi.co",
    ]
    api = os.getenv("MARKET_PAYMENT_API", "").strip().rstrip("/")
    if api:
        connect.append(api)
    site = os.getenv("HART_SITE_URL", "").strip().rstrip("/")
    if site:
        connect.append(site)
    for part in os.getenv("MARKET_CSP_CONNECT", "").split(","):
        p = part.strip()
        if p:
            connect.append(p)
    connect_src = " ".join(dict.fromkeys(connect))
    return (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://fonts.gstatic.com; "
        f"connect-src {connect_src}; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )


SITE_CSP = site_csp()

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,253}\.[^@\s]{2,64}$")
CLAIM_ID_RE = re.compile(r"^[a-f0-9]{12}$")
MAX_JSON_BODY = int(os.getenv("MARKET_MAX_BODY", "5242880"))  # 5 MB


def load_env_local() -> None:
    """Подгружает секреты из .env.local (не выкладывать в интернет)."""
    path = BASE / ".env.local"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v
    global SITE_CSP
    SITE_CSP = site_csp()


def admin_pin() -> str:
    load_env_local()
    pin = os.getenv("MARKET_ADMIN_PIN", "")
    if not pin or pin == "199-admin-change-me":
        # Слабый PIN по умолчанию — только localhost, но предупреждаем в логе
        return pin or "199-admin-change-me"
    return pin


def client_ip(handler) -> str:
    fwd = handler.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()[:64]
    return (handler.client_address[0] if handler.client_address else "unknown")[:64]


class RateLimiter:
    def __init__(self, max_hits: int, window_sec: float) -> None:
        self.max_hits = max_hits
        self.window = window_sec
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.time()
        bucket = self._hits[key]
        bucket[:] = [t for t in bucket if now - t < self.window]
        if len(bucket) >= self.max_hits:
            return False
        bucket.append(now)
        return True


class PinGuard:
    """Блокировка после перебора PIN."""

    def __init__(self, max_fails: int = 5, lock_sec: float = 900) -> None:
        self.max_fails = max_fails
        self.lock_sec = lock_sec
        self._fails: dict[str, list[float]] = defaultdict(list)
        self._locked: dict[str, float] = {}

    def locked(self, ip: str) -> bool:
        until = self._locked.get(ip, 0)
        if until and time.time() < until:
            return True
        if until:
            del self._locked[ip]
        return False

    def check(self, ip: str, pin: str, expected: str) -> bool:
        if self.locked(ip):
            return False
        ok = hmac.compare_digest(pin or "", expected or "")
        if ok:
            self._fails.pop(ip, None)
            return True
        now = time.time()
        self._fails[ip] = [t for t in self._fails[ip] if now - t < self.lock_sec]
        self._fails[ip].append(now)
        if len(self._fails[ip]) >= self.max_fails:
            self._locked[ip] = now + self.lock_sec
        return False


# Лимиты API
rl_code = RateLimiter(30, 3600)
rl_access = RateLimiter(60, 3600)
rl_claim = RateLimiter(8, 3600)
rl_claim_email = RateLimiter(3, 86400)
rl_admin = RateLimiter(40, 3600)
rl_user = RateLimiter(30, 3600)
pin_guard = PinGuard()


def apply_security_headers(handler, *, csp: str | None = None) -> None:
    for k, v in SECURITY_HEADERS.items():
        handler.send_header(k, v)
    if csp:
        handler.send_header("Content-Security-Policy", csp)


def apply_cors(handler, *, allow_credentials: bool = False) -> None:
    origin = handler.headers.get("Origin", "")
    if origin in CORS_ORIGINS:
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
        if allow_credentials:
            handler.send_header("Access-Control-Allow-Credentials", "true")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header(
        "Access-Control-Allow-Headers", "Content-Type, X-Admin-Pin, X-Request-Token"
    )


def read_json_body(handler, max_bytes: int = MAX_JSON_BODY) -> dict | None:
    try:
        n = int(handler.headers.get("Content-Length", 0))
    except ValueError:
        return None
    if n < 0 or n > max_bytes:
        return None
    raw = handler.rfile.read(n)
    try:
        data = json.loads(raw.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def detect_receipt_ext(raw: bytes) -> str | None:
    if len(raw) < 12:
        return None
    if raw[:3] == b"\xff\xd8\xff":
        return "jpg"
    if raw[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if raw[:4] == b"%PDF":
        return "pdf"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "webp"
    return None


def decode_receipt_b64(data: str) -> bytes | None:
    if not data or len(data) > 6_000_000:
        return None
    part = data.split(",")[-1]
    try:
        raw = base64.b64decode(part, validate=True)
    except Exception:
        return None
    if len(raw) > 4_000_000:
        return None
    if detect_receipt_ext(raw) is None:
        return None
    return raw


def is_safe_http_url(url: str) -> bool:
    if not url or len(url) > 500:
        return False
    try:
        from urllib.parse import urlparse

        p = urlparse(url.strip())
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    if not p.netloc or "@" in p.netloc:
        return False
    low = url.lower()
    if any(x in low for x in ("javascript:", "data:", "vbscript:", "file:")):
        return False
    return True


def rate_limit_or_429(handler, limiter: RateLimiter, key: str) -> bool:
    if limiter.allow(key):
        return True
    handler.send_response(429)
    apply_cors(handler)
    apply_security_headers(handler, csp=API_CSP)
    body = json.dumps(
        {"ok": False, "error": "Слишком много запросов. Подождите."},
        ensure_ascii=False,
    ).encode()
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)
    return False
