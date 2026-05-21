#!/usr/bin/env python3
"""
Google Search Console + Яндекс.Вебмастер + TXT в REG.RU (браузер).
Запуск: python scripts/seo_browser_setup.py
Нужен вход в Google и Яндекс в профиле Yandex Browser (или войдёте вручную).
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

DOMAIN = "hart-club.ru"
SITE = f"https://{DOMAIN}"
SITEMAP = f"{SITE}/sitemap.xml"
YANDEX_PROFILE = Path.home() / "AppData/Local" / "Yandex" / "YandexBrowser" / "User Data"
OUT = Path(__file__).resolve().parent.parent / "seo-verification-codes.txt"


def run_playwright() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("pip install playwright && playwright install chromium")
        return 1

    codes: list[str] = []

    with sync_playwright() as p:
        launch_kw = {"headless": False, "locale": "ru-RU"}
        if YANDEX_PROFILE.is_dir():
            try:
                ctx = p.chromium.launch_persistent_context(
                    str(YANDEX_PROFILE),
                    channel="chrome",
                    headless=False,
                    args=["--profile-directory=Default"],
                )
                page = ctx.pages[0] if ctx.pages else ctx.new_page()
            except Exception as e:
                print("Persistent profile failed:", e)
                browser = p.chromium.launch(**launch_kw)
                ctx = browser.new_context()
                page = ctx.new_page()
        else:
            browser = p.chromium.launch(**launch_kw)
            ctx = browser.new_context()
            page = ctx.new_page()

        # --- Google Search Console ---
        print("→ Google Search Console…")
        page.goto("https://search.google.com/search-console/welcome", timeout=60000)
        time.sleep(4)
        try:
            page.get_by_role("link", name=re.compile("добав|add|property", re.I)).first.click(timeout=8000)
        except Exception:
            pass
        time.sleep(2)
        try:
            page.get_by_text(re.compile("Домен|Domain", re.I)).first.click(timeout=5000)
        except Exception:
            pass
        time.sleep(1)
        inp = page.locator('input[type="text"]').first
        inp.fill(DOMAIN, timeout=10000)
        time.sleep(1)
        try:
            page.get_by_role("button", name=re.compile("продолж|continue|далее", re.I)).first.click(timeout=5000)
        except Exception:
            page.keyboard.press("Enter")
        time.sleep(3)
        body = page.content()
        m = re.search(r"google-site-verification=[A-Za-z0-9_\-]+", body)
        if m:
            codes.append(f"GOOGLE_DNS_TXT={m.group(0)}")
            print("  Google TXT:", m.group(0))
        else:
            codes.append("GOOGLE=откройте DNS-запись вручную на экране и скопируйте TXT")

        # --- Yandex Webmaster ---
        print("→ Яндекс.Вебмастер…")
        page.goto("https://webmaster.yandex.ru/sites/add/", timeout=60000)
        time.sleep(3)
        try:
            page.locator('input[name="host"], input[type="text"]').first.fill(SITE, timeout=8000)
            page.get_by_role("button", name=re.compile("добав|add", re.I)).first.click(timeout=5000)
        except Exception:
            pass
        time.sleep(4)
        body = page.content()
        m = re.search(r'content="([a-f0-9]{16,})"\s+name="yandex-verification"', body)
        if not m:
            m = re.search(r'yandex-verification["\']?\s*content=["\']([a-f0-9]+)', body)
        if m:
            codes.append(f"YANDEX_META={m.group(1)}")
            print("  Yandex meta:", m.group(1))
        else:
            codes.append("YANDEX=скопируйте meta verification с экрана")

        time.sleep(2)
        ctx.close()

    OUT.write_text("\n".join(codes) + "\n", encoding="utf-8")
    print("Saved", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(run_playwright())
