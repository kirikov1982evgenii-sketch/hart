# Вставьте в WSGI-файл на PythonAnywhere (Web → WSGI configuration)
import sys

path = "/home/eg1982/klub-znaniy-hart"
if path not in sys.path:
    sys.path.insert(0, path)

from wsgi import application
