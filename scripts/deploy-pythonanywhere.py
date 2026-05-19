#!/usr/bin/env python3
"""Деплой на PythonAnywhere (eg1982) через API."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USERNAME = "eg1982"
HOST = "www.pythonanywhere.com"
DOMAIN = f"{USERNAME}.pythonanywhere.com"
REPO_DIR = f"/home/{USERNAME}/hart"
WSGI_PATH = f"/var/www/{USERNAME}_pythonanywhere_com_wsgi.py"
TOKEN_FILE = Path.home() / "Desktop" / "pythonanywhere-token.txt"
BASE = Path(__file__).resolve().parent.parent


def token() -> str:
    for p in (TOKEN_FILE, BASE / "pythonanywhere-token.txt"):
        if p.is_file():
            t = p.read_text(encoding="utf-8").strip().splitlines()[0].strip()
            if t and not t.startswith("#") and "вставьте" not in t.lower():
                return t
    print(f"Нужен API-токен: {TOKEN_FILE}")
    print("https://www.pythonanywhere.com/account/#api_token - Create - paste into file")
    sys.exit(1)


def api(method: str, path: str, tok: str, data: bytes | None = None, form: dict | None = None) -> tuple[int, str]:
    url = f"https://{HOST}{path}"
    headers = {"Authorization": f"Token {tok}"}
    if form:
        boundary = "----hartboundary"
        body = b""
        for k, v in form.items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
            body += f"{v}\r\n".encode()
        body += f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        data = body
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")


def upload_file(tok: str, remote_path: str, content: bytes) -> None:
    encoded = urllib.parse.quote(remote_path, safe="")
    boundary = "----hartupload"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="content"; filename="f"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    url = f"https://{HOST}/api/v0/user/{USERNAME}/files/path{encoded}"
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Token {tok}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            print("  uploaded", remote_path, r.status)
    except urllib.error.HTTPError as e:
        print("  FAIL", remote_path, e.code, e.read().decode()[:200])


def run_console(tok: str, command: str) -> None:
    code, body = api("POST", f"/api/v0/user/{USERNAME}/consoles/", tok, form={"executable": "bash"})
    print("console", code, body[:200])
    data = json.loads(body)
    cid = data["id"]
    time.sleep(2)
    for line in command.split("\n"):
        api(
            "POST",
            f"/api/v0/user/{USERNAME}/consoles/{cid}/send_input/",
            tok,
            form={"input": line + "\n"},
        )
        time.sleep(1)
    time.sleep(8)
    code, out = api("GET", f"/api/v0/user/{USERNAME}/consoles/{cid}/get_latest_output/", tok)
    print(out[-1500:])


def main() -> None:
    tok = token()
    print("Deploy to", DOMAIN)

    run_console(
        tok,
        f"cd ~ && (test -d hart && cd hart && git pull) || git clone https://github.com/kirikov1982evgenii-sketch/hart.git",
    )

    env_local = BASE / ".env.local"
    if not env_local.is_file():
        env_local = Path.home() / "Desktop" / "Свободный-Маркет-Интерактив" / ".env.local"
    if env_local.is_file():
        upload_file(tok, f"{REPO_DIR}/.env.local", env_local.read_bytes())
    else:
        print("WARN: no .env.local to upload")

    wsgi = (BASE / "pythonanywhere-wsgi-snippet.py").read_text(encoding="utf-8")
    wsgi = wsgi.replace(
        'path = "/home/eg1982/hart"',
        f'path = "{REPO_DIR}"',
    )
    upload_file(tok, WSGI_PATH, wsgi.encode("utf-8"))

    code, body = api("POST", f"/api/v0/user/{USERNAME}/webapps/{DOMAIN}/reload/", tok)
    print("reload", code, body[:200])

    time.sleep(3)
    try:
        with urllib.request.urlopen(f"https://{DOMAIN}/api/health", timeout=30) as r:
            print("health", r.read().decode())
    except Exception as e:
        print("health check:", e)


if __name__ == "__main__":
    main()
