#!/usr/bin/env python3
"""Безопасная раздача статики: без data/receipts, с заголовками и лимитом запросов."""
from __future__ import annotations

import os
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from security_common import SITE_CSP, RateLimiter, apply_security_headers, client_ip, load_env_local
from server_common import bind_host, service_port

BASE = Path(__file__).resolve().parent
load_env_local()
PORT = service_port("SITE_PORT", 8765)
HOST = bind_host()

FORBIDDEN_PREFIXES = (
    "/data/receipts",
    "/data/payment_claims",
    "/.env",
    "/.cursor",
    "/scripts/",
    "/__pycache__/",
)
ALLOWED_DATA_FILES = {"/data/resources.json", "/data/i18n.json"}
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

    def do_GET(self):
        ip = client_ip(self)
        if not rl_site.allow(ip):
            self.send_error(429, "Too Many Requests")
            return
        norm = normalize_path(self.path)
        if not path_allowed(norm):
            self.send_error(403, "Forbidden")
            return
        return super().do_GET()

    def do_HEAD(self):
        norm = normalize_path(self.path)
        if not path_allowed(norm):
            self.send_error(403, "Forbidden")
            return
        return super().do_HEAD()

    def list_directory(self, path):
        self.send_error(403, "Directory listing forbidden")
        return None


def main():
    print(f"Secure site http://{HOST}:{PORT}", flush=True)
    srv = ThreadingHTTPServer((HOST, PORT), SecureHandler)
    srv.serve_forever()


if __name__ == "__main__":
    main()
