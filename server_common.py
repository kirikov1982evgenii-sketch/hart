"""Общие настройки запуска серверов (локально и на хостинге)."""
from __future__ import annotations

import os


def bind_host() -> str:
    explicit = os.getenv("BIND_HOST", "").strip()
    if explicit:
        return explicit
    if os.getenv("DEV_LOCAL", "").lower() in ("1", "true", "yes"):
        return "127.0.0.1"
    return "0.0.0.0"


def service_port(env_name: str, default: int) -> int:
    """PORT — стандарт Render/Railway; иначе именованная переменная."""
    raw = os.getenv("PORT") or os.getenv(env_name, str(default))
    return int(raw)
