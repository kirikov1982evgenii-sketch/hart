#!/usr/bin/env python3
"""Push SEO files + trigger Pages deploy via git + GitHub API."""
from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def git_token() -> str:
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        capture_output=True,
        text=True,
        timeout=20,
    )
    for line in p.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("Нет git credential для github.com")


def gh(method: str, path: str, body: dict | None = None) -> dict:
    tok = git_token()
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> None:
    subprocess.run(["git", "add", "sitemap.xml", "robots.txt", "indexnow-key.txt", "*.txt"], cwd=REPO, check=False)
    subprocess.run(
        ["git", "commit", "-m", "SEO: IndexNow key and sitemap ping", "--allow-empty"],
        cwd=REPO,
        capture_output=True,
    )
    subprocess.run(["git", "push", "origin", "main"], cwd=REPO, check=True)
    try:
        gh("POST", "/repos/kirikov1982evgenii-sketch/hart/actions/workflows/deploy-site.yml/dispatches", {"ref": "main"})
        print("Triggered deploy-site workflow")
    except Exception as e:
        print("Workflow dispatch:", e)
    try:
        pages = gh("GET", "/repos/kirikov1982evgenii-sketch/hart/pages")
        print("Pages URL:", pages.get("html_url"), "HTTPS:", pages.get("https_certificate", {}).get("state"))
    except Exception as e:
        print("Pages info:", e)


if __name__ == "__main__":
    main()
