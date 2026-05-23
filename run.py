#!/usr/bin/env python3
"""Один запуск: API + сайт + браузер."""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

BASE = Path(__file__).resolve().parent
os.chdir(BASE)
sys.path.insert(0, str(BASE))
os.environ["DEV_LOCAL"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

HOME = "http://127.0.0.1:8765/"
CABINET = HOME + "cabinet.html"


def course_url(course_id: str = "облако-знаний", n: int = 1) -> str:
    from urllib.parse import quote

    q = f"id={quote(course_id)}&learn=1&n={n}"
    return f"http://127.0.0.1:8765/course.html?{q}"


def free_ports() -> None:
    if sys.platform != "win32":
        return
    for port in (8765, 8766):
        try:
            out = subprocess.check_output(
                ["netstat", "-ano"],
                text=True,
                errors="ignore",
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            for line in out.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        if pid.isdigit():
                            subprocess.run(
                                ["taskkill", "/PID", pid, "/F"],
                                capture_output=True,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                            )
        except Exception:
            pass
    time.sleep(1)


def wait_server(url: str, seconds: int = 45) -> bool:
    import urllib.request

    for i in range(seconds):
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(1)
            if i % 5 == 4:
                print(f"  ждём сервер… ({i + 1}/{seconds} сек)", flush=True)
    return False


def open_browser(url: str) -> None:
    print("Открываю:", url, flush=True)
    if sys.platform == "win32":
        try:
            os.startfile(url)  # type: ignore[attr-defined]
            return
        except Exception:
            pass
    webbrowser.open(url)


def run_api() -> None:
    import payment_server

    payment_server.main()


def run_site() -> None:
    import site_server

    site_server.main()


def main() -> None:
    print("=" * 52)
    print("  КЛУБ ЗНАНИЙ HART")
    print("=" * 52)
    print("Папка:", BASE)
    print()

    free_ports()

    threading.Thread(target=run_api, daemon=True).start()
    time.sleep(2)
    threading.Thread(target=run_site, daemon=True).start()

    print("Запуск… подождите до 45 сек.")
    if not wait_server(HOME):
        print("\n*** ОШИБКА: сайт не ответил ***")
        print("1) Закройте другие копии HART / Python")
        print("2) Запустите снова ЗАПУСК.bat")
        print("3) Если снова ошибка — пришлите текст этого окна")
        input("\nEnter — выход…")
        sys.exit(1)

    # Автовход в кабинет (как в браузере при открытии cabinet.html)
    try:
        import urllib.request

        urllib.request.urlopen("http://127.0.0.1:8766/api/dev/session", timeout=5)
    except Exception:
        pass

    print("\n*** ГОТОВО ***")
    print("Кабинет:  ", CABINET)
    print("Сайт:     ", HOME)
    print("Курс №1:  ", course_url("облако-знаний", 1))
    open_browser(CABINET)

    print("\n" + "=" * 52)
    print("  НЕ ЗАКРЫВАЙТЕ ЭТО ОКНО — иначе сайт выключится")
    print("  Остановка: закройте окно или Ctrl+C")
    print("=" * 52 + "\n")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Стоп.")


if __name__ == "__main__":
    main()
