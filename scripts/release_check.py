#!/usr/bin/env python3
"""Перед продажей: python scripts/release_check.py"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    steps = [
        ([sys.executable, str(ROOT / "scripts" / "qa_audit.py")], "QA контент"),
    ]
    for cmd, label in steps:
        print(f"\n--- {label} ---")
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode:
            print(f"FAIL: {label}")
            return 1
    print("\nOK: проверка контента пройдена")
    return 0


if __name__ == "__main__":
    sys.exit(main())
