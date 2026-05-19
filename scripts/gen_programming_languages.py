#!/usr/bin/env python3
"""Генерация data/programming_languages_courses.json — отдельный курс на каждый ЯП."""
from __future__ import annotations

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "data" / "programming_languages_courses.json"

# name, slug, url, focus (кратко), paradigm hint
LANGUAGES = [
    ("Python", "python", "https://docs.python.org/3/tutorial/", "универсальная разработка и data science"),
    ("JavaScript", "javascript", "https://javascript.info/", "веб, браузер и Node.js"),
    ("TypeScript", "typescript", "https://www.typescriptlang.org/docs/", "типизированный JavaScript для крупных проектов"),
    ("Java", "java", "https://dev.java/learn/", "корпоративные системы и Android"),
    ("C", "c", "https://en.cppreference.com/w/c", "системное программирование и основы"),
    ("C++", "cpp", "https://en.cppreference.com/w/cpp", "производительность, игры, embedded"),
    ("C#", "csharp", "https://learn.microsoft.com/dotnet/csharp/", ".NET, Unity, enterprise"),
    ("Go", "go", "https://go.dev/tour/", "микросервисы и облачная инфраструктура"),
    ("Rust", "rust", "https://doc.rust-lang.org/book/", "безопасность памяти и системный код"),
    ("Kotlin", "kotlin", "https://kotlinlang.org/docs/getting-started.html", "Android и JVM"),
    ("Swift", "swift", "https://docs.swift.org/swift-book/", "iOS, macOS, SwiftUI"),
    ("Ruby", "ruby", "https://www.ruby-lang.org/en/documentation/", "Rails и быстрый прототип"),
    ("PHP", "php", "https://www.php.net/manual/en/getting-started.php", "веб-бэкенд и CMS"),
    ("Scala", "scala", "https://docs.scala-lang.org/getting-started.html", "JVM и функциональный стиль"),
    ("R", "r", "https://cran.r-project.org/manuals.html", "статистика и визуализация данных"),
    ("Julia", "julia", "https://docs.julialang.org/en/v1/manual/getting-started/", "научные вычисления"),
    ("Dart", "dart", "https://dart.dev/guides", "Flutter и кроссплатформа"),
    ("Lua", "lua", "https://www.lua.org/pil/", "скрипты в играх и embedded"),
    ("Perl", "perl", "https://perldoc.perl.org/perlintro", "автоматизация и legacy"),
    ("Haskell", "haskell", "https://www.haskell.org/documentation/", "чистое функциональное программирование"),
    ("Elixir", "elixir", "https://elixir-lang.org/getting-started/introduction.html", "OTP, Phoenix, отказоустойчивость"),
    ("Clojure", "clojure", "https://clojure.org/guides/getting_started", "Lisp на JVM"),
    ("F#", "fsharp", "https://learn.microsoft.com/dotnet/fsharp/", "функциональный .NET"),
    ("Objective-C", "objective-c", "https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ProgrammingWithObjectiveC/", "legacy iOS/macOS"),
    ("Assembly (x86)", "assembly", "https://cs.lmu.edu/~ray/notes/nasmtutorial/", "низкоуровневые основы"),
    ("SQL", "sql", "https://sqlbolt.com/", "запросы к реляционным БД"),
    ("Bash", "bash", "https://www.gnu.org/software/bash/manual/html_node/", "автоматизация в Linux"),
    ("PowerShell", "powershell", "https://learn.microsoft.com/powershell/scripting/overview", "администрирование Windows"),
    ("Zig", "zig", "https://ziglang.org/learn/", "системный код без скрытых аллокаторов"),
    ("Fortran", "fortran", "https://fortran-lang.org/learn/", "научные расчёты"),
    ("Solidity", "solidity", "https://docs.soliditylang.org/en/latest/introduction-to-smart-contracts.html", "смарт-контракты Ethereum"),
    ("VBA", "vba", "https://learn.microsoft.com/office/vba/api/overview/", "макросы Excel и Office"),
    ("Prolog", "prolog", "https://www.swi-prolog.org/pldoc/doc_for?object=manual", "логическое программирование"),
    ("Erlang", "erlang", "https://www.erlang.org/getting_started", "распределённые телеком-системы"),
    ("OCaml", "ocaml", "https://ocaml.org/docs", "функциональный язык с типами"),
    ("Racket", "racket", "https://docs.racket-lang.org/getting-started/", "обучение и DSL"),
    ("Scheme", "scheme", "https://scheme.org/", "Lisp для академии"),
    ("Groovy", "groovy", "https://groovy-lang.org/documentation.html", "JVM-скрипты и Gradle"),
    ("Visual Basic .NET", "vbnet", "https://learn.microsoft.com/dotnet/visual-basic/", "legacy .NET приложения"),
    ("COBOL", "cobol", "https://www.ibm.com/docs/en/cobol-zos", "банки и мейнфреймы"),
    ("Pascal", "pascal", "https://www.freepascal.org/docs.html", "алгоритмы и Free Pascal"),
    ("Ada", "ada", "https://learn.adacore.com/", "встраиваемые и критичные системы"),
    ("Lisp", "lisp", "https://lispcookbook.github.io/cl-cookbook/", "метапрограммирование"),
    ("AWK", "awk", "https://www.gnu.org/software/gawk/manual/gawk.html", "обработка текста в Unix"),
    ("Crystal", "crystal", "https://crystal-lang.org/reference/", "Ruby-подобный, компилируемый"),
    ("Nim", "nim", "https://nim-lang.org/docs/tut1.html", "метапрограммирование и C-производительность"),
    ("V", "vlang", "https://github.com/vlang/v/blob/master/doc/docs.md", "быстрая компиляция"),
    ("Elm", "elm", "https://guide.elm-lang.org/", "фронтенд без runtime-ошибок"),
    ("Tcl", "tcl", "https://www.tcl-lang.org/man/tcl8.6/Tutorial/tutorial.html", "скрипты и GUI Tk"),
    ("MATLAB", "matlab", "https://www.mathworks.com/help/matlab/getting-started-with-matlab.html", "инженерия и моделирование"),
    ("HTML", "html", "https://developer.mozilla.org/en-US/docs/Web/HTML", "разметка веб-страниц"),
    ("CSS", "css", "https://developer.mozilla.org/en-US/docs/Web/CSS", "стили и вёрстка"),
    ("Verilog", "verilog", "https://www.chipverify.com/verilog/verilog-tutorial", "цифровые схемы и FPGA"),
    ("VHDL", "vhdl", "https://www.nandland.com/vhdl/tutorials/tutorial-introduction-to-vhdl.html", "аппаратное описание"),
    ("Smalltalk", "smalltalk", "https://book.pharo.org/", "ООП и Pharo"),
    ("Forth", "forth", "https://www.forth.com/starting-forth/", "стековый язык embedded"),
]


QUERY_SLUGS = {"sql"}
MARKUP_SLUGS = {"html", "css"}
SCRIPT_SLUGS = {"bash", "powershell", "awk", "tcl"}
FUNC_SLUGS = {
    "haskell",
    "prolog",
    "elixir",
    "erlang",
    "clojure",
    "scheme",
    "lisp",
    "fsharp",
    "ocaml",
}
SYSTEM_SLUGS = {"c", "cpp", "rust", "zig", "assembly", "verilog", "vhdl", "fortran", "ada"}


def module_3(name: str, slug: str) -> str:
    if slug in QUERY_SLUGS:
        return f"Модуль 3. Запросы: SELECT, JOIN, агрегация в {name}"
    if slug in MARKUP_SLUGS:
        return f"Модуль 3. Структура документа и ключевые теги {name}"
    if slug in SCRIPT_SLUGS:
        return f"Модуль 3. Скрипты, условия и автоматизация в {name}"
    return f"Модуль 3. Управление потоком: условия, циклы, обработка ошибок"


def module_6(name: str, slug: str) -> str:
    if slug in QUERY_SLUGS | MARKUP_SLUGS:
        return f"Модуль 6. Практические паттерны и типовые задачи в {name}"
    if slug in FUNC_SLUGS:
        return f"Модуль 6. Парадигмы и идиомы {name}"
    if slug in SYSTEM_SLUGS:
        return f"Модуль 6. Память, типы и идиомы {name}"
    if slug == "go":
        return "Модуль 6. Интерфейсы, горутины и идиомы Go"
    return f"Модуль 6. Объектно-ориентированный подход в {name}"


def course_for(name: str, slug: str, url: str, focus: str) -> dict:
    title = f"Изучение {name} — полный курс HART"
    tag = name.split()[0] if " " in name else name
    return {
        "cat": "courses",
        "premium": True,
        "title": title,
        "url": url,
        "desc": f"Отдельная программа по языку {name}: {focus}.",
        "tags": ["IT", "программирование", tag, "языки программирования"],
        "level": "Начальный → Средний",
        "duration": "Трек · 25–45 часов",
        "format": "Модули + практика + официальные материалы",
        "provider": "Клуб знаний HART",
        "id": f"hart-lang-{slug}",
        "modules": [
            f"Модуль 1. Введение в {name}: зачем язык, среда, первая программа",
            f"Модуль 2. Синтаксис {name}: типы, переменные, операторы",
            module_3(name, slug),
            f"Модуль 4. Функции, модули и организация кода",
            f"Модуль 5. Структуры данных и стандартная библиотека",
            module_6(name, slug),
            f"Модуль 7. Практика: мини-проект и code review",
            f"Модуль 8. Best practices, отладка и следующий уровень",
        ],
        "learn": [
            f"Писать рабочий код на {name} с нуля",
            "Читать официальную документацию и примеры",
            "Решать типовые задачи и мини-проекты",
            f"Понимать, где применяется {name} ({focus})",
            "Готовиться к углублённым курсам и собеседованиям",
        ],
        "about": (
            f"Отдельный курс Клуба знаний HART по языку {name}. "
            f"Только {name} — без смешения с другими языками, шаг за шагом.\n\n"
            f"Фокус: {focus}. Программа из 8 модулей: от установки среды до мини-проекта. "
            f"После оплаты откроется ссылка на проверенный ресурс и материалы курса на сайте.\n\n"
            f"Ориентир: 4–6 недель при 5–7 часах в неделю."
        ),
    }


def main() -> None:
    courses = [course_for(*row) for row in LANGUAGES]
    OUT.write_text(json.dumps(courses, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Wrote", len(courses), "courses to", OUT)


if __name__ == "__main__":
    main()
