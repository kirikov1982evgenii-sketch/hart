#!/usr/bin/env python3
"""WSGI для PythonAnywhere: API оплат + webhook Telegram (без Render и без карты)."""
from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from payment_server import Handler, load_env_local
from telegram_bot import process_update

_server: ThreadingHTTPServer | None = None
_lock = threading.Lock()
API_HOST = "127.0.0.1"
API_PORT = int(os.getenv("INTERNAL_API_PORT") or "18080")


def _ensure_api() -> None:
    global _server
    with _lock:
        if _server is not None:
            return
        load_env_local()
        os.environ.setdefault("BIND_HOST", API_HOST)
        _server = ThreadingHTTPServer((API_HOST, API_PORT), Handler)
        threading.Thread(target=_server.serve_forever, daemon=True).start()


def _proxy(environ, start_response):
    _ensure_api()
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "") or "/"
    qs = environ.get("QUERY_STRING", "")
    url = f"http://{API_HOST}:{API_PORT}{path}"
    if qs:
        url += "?" + qs
    length = int(environ.get("CONTENT_LENGTH") or 0)
    body = environ["wsgi.input"].read(length) if length else None
    headers = {}
    for k, v in environ.items():
        if k.startswith("HTTP_") and k != "HTTP_HOST":
            headers[k[5:].replace("_", "-")] = v
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            status = f"{resp.status} {resp.reason}"
            hdrs = list(resp.headers.items())
            payload = resp.read()
            start_response(status, hdrs)
            return [payload]
    except urllib.error.HTTPError as e:
        payload = e.read()
        start_response(f"{e.code} {e.reason}", list(e.headers.items()))
        return [payload]


def _telegram_webhook(environ, start_response):
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
        raw = environ["wsgi.input"].read(length) if length else b"{}"
        update = json.loads(raw.decode("utf-8") or "{}")
        process_update(update)
        start_response("200 OK", [("Content-Type", "application/json")])
        return [b'{"ok":true}']
    except Exception as e:
        start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
        return [str(e).encode("utf-8")]


def application(environ, start_response):
    path = environ.get("PATH_INFO", "") or "/"
    if path == "/telegram-webhook" and environ.get("REQUEST_METHOD") == "POST":
        return _telegram_webhook(environ, start_response)
    return _proxy(environ, start_response)
