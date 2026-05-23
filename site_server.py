#!/usr/bin/env python3
"""Безопасная раздача статики + API курса (без загрузки 2.7 МБ в браузере)."""
from __future__ import annotations

import http.client
import json
import os
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from security_common import SITE_CSP, RateLimiter, apply_security_headers, client_ip, load_env_local
from server_common import bind_host, service_port

BASE = Path(__file__).resolve().parent
load_env_local()
PORT = service_port("SITE_PORT", 8765)
API_PORT = service_port("PAYMENT_API_PORT", 8766)
HOST = bind_host()
API_HOST = "127.0.0.1"
RESOURCES_FILE = BASE / "data" / "resources.json"
_resources_cache: tuple[float, dict] | None = None

FORBIDDEN_PREFIXES = (
    "/data/receipts",
    "/data/payment_claims",
    "/data/users.json",
    "/.env",
    "/.cursor",
    "/scripts/",
    "/__pycache__/",
)
ALLOWED_DATA_FILES = {"/data/resources.json", "/data/catalog.json", "/data/i18n.json"}
BLOCKED_EXTENSIONS = {".py", ".pyc", ".env", ".local", ".jsonl", ".md"}

rl_site = RateLimiter(200, 60)


def normalize_path(path: str) -> str:
    p = urllib.parse.unquote(path.split("?", 1)[0])
    if not p.startswith("/"):
        p = "/" + p
    parts = []
    for seg in p.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            return ""
        parts.append(seg)
    return "/" + "/".join(parts) if parts else "/"


def path_allowed(norm: str) -> bool:
    if not norm:
        return False
    low = norm.lower()
    for pref in FORBIDDEN_PREFIXES:
        if low.startswith(pref):
            return False
    if "/." in low or low.startswith("/."):
        return False
    if low.startswith("/data/"):
        return low in ALLOWED_DATA_FILES
    if low.endswith(".env") or low.endswith(".env.local"):
        return False
    ext = Path(low).suffix.lower()
    if ext in BLOCKED_EXTENSIONS:
        return False
    return True


PAGE_ALIASES = {
    "/cabinet": "/cabinet.html",
    "/course": "/course.html",
    "/pay": "/pay.html",
    "/support": "/support.html",
    "/owner": "/owner.html",
    "/admin-payments": "/admin-payments.html",
    "/admin": "/admin-cabinet.html",
    "/admin-cabinet": "/admin-cabinet.html",
    "/open-course": "/open-course.html",
}


def resolve_public_path(norm: str) -> str:
    if not norm or norm == "/":
        return "/index.html"
    if norm in PAGE_ALIASES:
        return PAGE_ALIASES[norm]
    rel = norm.lstrip("/")
    direct = BASE / rel
    if direct.is_file():
        return norm
    ext = Path(norm).suffix.lower()
    if not ext:
        html = BASE / f"{rel}.html"
        if html.is_file():
            return f"/{rel}.html"
    if not ext or ext == ".html":
        if (BASE / "404.html").is_file():
            return "/404.html"
    return norm


def load_resources() -> dict:
    global _resources_cache
    if not RESOURCES_FILE.is_file():
        return {"resources": []}
    mtime = RESOURCES_FILE.stat().st_mtime
    if _resources_cache and _resources_cache[0] == mtime:
        return _resources_cache[1]
    data = json.loads(RESOURCES_FILE.read_text(encoding="utf-8"))
    _resources_cache = (mtime, data)
    return data


def find_course(course_id: str) -> dict | None:
    cid = (course_id or "").strip()[:120]
    if not cid:
        return None
    for r in load_resources().get("resources", []):
        if r.get("id") == cid:
            return r
    return None


class SecureHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE), **kwargs)

    def log_message(self, fmt, *args):
        pass

    def end_headers(self):
        apply_security_headers(self, csp=SITE_CSP)
        path = urllib.parse.unquote(self.path.split("?", 1)[0]).lower()
        if path.endswith((".html", ".js", ".css")) or path.endswith("/"):
            self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    def _json(self, code: int, obj: dict) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _serve_catalog_api(self) -> bool:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/catalog":
            return False
        cat_file = BASE / "data" / "catalog.json"
        if cat_file.is_file():
            raw = cat_file.read_bytes()
        else:
            data = load_resources()
            slim = [{k: v for k, v in r.items() if k != "lessons"} for r in data.get("resources", [])]
            raw = json.dumps(
                {"meta": data.get("meta"), "categories": data.get("categories"), "resources": slim},
                ensure_ascii=False,
            ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
        return True

    def _serve_course_api(self) -> bool:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/course":
            return False
        q = urllib.parse.parse_qs(parsed.query)
        cid = (q.get("id") or [""])[0]
        course = find_course(cid)
        if not course:
            self._json(404, {"ok": False, "error": "Курс не найден"})
            return True
        self._json(200, {"ok": True, "course": course})
        return True

    def _proxy_api(self, method: str) -> bool:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/api/course", "/api/catalog"):
            return False
        if not parsed.path.startswith("/api/"):
            return False
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length > 0 else None
        conn = http.client.HTTPConnection(API_HOST, API_PORT, timeout=30)
        headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
        try:
            conn.request(method, self.path, body=body, headers=headers)
            resp = conn.getresponse()
            self.send_response(resp.status)
            for k, v in resp.getheaders():
                if k.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(k, v)
            self.end_headers()
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
        except Exception:
            self.send_error(502, "API unavailable")
        finally:
            conn.close()
        return True

    def _prepare_path(self) -> str | None:
        parsed = urllib.parse.urlparse(self.path)
        norm = normalize_path(parsed.path)
        if not path_allowed(norm):
            return None
        resolved = resolve_public_path(norm)
        self.path = resolved + (f"?{parsed.query}" if parsed.query else "")
        return resolved

    def do_OPTIONS(self):
        if self._serve_course_api() or self._proxy_api("OPTIONS"):
            return
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        if self._proxy_api("POST"):
            return
        self.send_error(405, "Method Not Allowed")

    def do_GET(self):
        if self._serve_catalog_api():
            return
        if self._serve_course_api():
            return
        if self._proxy_api("GET"):
            return
        ip = client_ip(self)
        if not rl_site.allow(ip):
            self.send_error(429, "Too Many Requests")
            return
        if self._prepare_path() is None:
            self.send_error(403, "Forbidden")
            return
        return super().do_GET()

    def do_HEAD(self):
        if self._prepare_path() is None:
            self.send_error(403, "Forbidden")
            return
        return super().do_HEAD()

    def list_directory(self, path):
        self.send_error(403, "Directory listing forbidden")
        return None


def main():
    print(f"Secure site http://{HOST}:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), SecureHandler).serve_forever()


if __name__ == "__main__":
    main()
