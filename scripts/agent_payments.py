#!/usr/bin/env python3
"""Проверка оплат для агента Cursor: список, просмотр чека, подтверждение."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RECEIPTS = BASE / "data" / "receipts"
CLAIMS_FILE = BASE / "data" / "payment_claims.json"
DEFAULT_API = os.getenv("PAYMENT_API_URL", "http://127.0.0.1:8766")
def load_pin() -> str:
    env_path = BASE / ".env.local"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("MARKET_ADMIN_PIN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    pin = os.getenv("MARKET_ADMIN_PIN", "")
    if pin:
        return pin
    return "199-admin-change-me"


def api(method: str, path: str, body: dict | None = None) -> dict:
    url = DEFAULT_API.rstrip("/") + path
    headers = {"X-Admin-Pin": load_pin()}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print("Ошибка API (запущен ли payment_server.py?):", e, file=sys.stderr)
        sys.exit(2)


def cmd_list(_: argparse.Namespace) -> None:
    out = api("GET", "/api/pending")
    if not out.get("ok"):
        print(out.get("error", out))
        sys.exit(1)
    claims = out.get("claims", [])
    if not claims:
        print("Нет заявок на проверке.")
        return
    for c in claims:
        rid = c.get("id", "")
        rf = c.get("receipt_file", "")
        rpath = RECEIPTS / rf if rf else None
        print("---")
        print(f"id:      {rid}")
        print(f"email:   {c.get('email')}")
        print(f"code:    {c.get('code')}")
        print(f"course:  {(c.get('course_title') or '')[:80]}")
        print(f"url:     {(c.get('course_url') or '')[:120]}")
        print(f"created: {c.get('created_at')}")
        print(f"receipt: {rpath if rpath and rpath.is_file() else 'нет файла'}")


def cmd_approve(args: argparse.Namespace) -> None:
    body: dict = {}
    if args.id:
        body["claim_id"] = args.id
    if args.code:
        body["code"] = args.code.upper()
    out = api("POST", "/api/approve", body)
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("ok") else 1)


def cmd_reject(args: argparse.Namespace) -> None:
    if not args.id:
        print("Нужен --id", file=sys.stderr)
        sys.exit(1)
    out = api("POST", "/api/reject", {"claim_id": args.id})
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out.get("ok") else 1)


def cmd_paths(_: argparse.Namespace) -> None:
    """Пути к чекам pending — для просмотра агентом (Read image)."""
    data = json.loads(CLAIMS_FILE.read_text(encoding="utf-8")) if CLAIMS_FILE.is_file() else {}
    pending = [c for c in data.get("claims", []) if c.get("status") == "pending"]
    if not pending:
        print("Нет pending.")
        return
    for c in pending:
        rf = c.get("receipt_file", "")
        p = RECEIPTS / rf if rf else None
        print(f"{c.get('id')}\t{p if p and p.is_file() else 'NO_RECEIPT'}")


def main() -> None:
    p = argparse.ArgumentParser(description="Проверка оплат каталога (агент Cursor)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="Список заявок pending").set_defaults(func=cmd_list)
    sub.add_parser("paths", help="Пути к файлам чеков").set_defaults(func=cmd_paths)
    a = sub.add_parser("approve", help="Подтвердить оплату")
    a.add_argument("--id", help="claim id")
    a.add_argument("--code", help="PAY-XXXXXXXX")
    a.set_defaults(func=cmd_approve)
    r = sub.add_parser("reject", help="Отклонить заявку")
    r.add_argument("--id", required=True)
    r.set_defaults(func=cmd_reject)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
