# WSGI на PythonAnywhere (eg1982) — автоклонирование при первом запуске
import os
import shutil
import subprocess
import sys

path = "/home/eg1982/hart"
repo = "https://github.com/kirikov1982evgenii-sketch/hart.git"
marker = os.path.join(path, "payment_server.py")

if not os.path.isfile(marker):
    tmp = "/tmp/hart_clone"
    shutil.rmtree(tmp, ignore_errors=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", repo, tmp],
        check=True,
        timeout=300,
    )
    os.makedirs(path, exist_ok=True)
    for name in os.listdir(tmp):
        src = os.path.join(tmp, name)
        dst = os.path.join(path, name)
        if name == ".env.local" and os.path.isfile(dst):
            continue
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    shutil.rmtree(tmp, ignore_errors=True)

if path not in sys.path:
    sys.path.insert(0, path)

from wsgi import application
