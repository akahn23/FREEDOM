"""Shared helpers for scripts/create_node.py and scripts/create_task_block.py (stdlib only)."""

import pathlib
import re
import string
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BACKEND_SRC = ROOT / "backend" / "src"
TEMPLATES = pathlib.Path(__file__).resolve().parent / "templates"
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def check_name(name: str, what: str) -> None:
    if not NAME_RE.match(name):
        fail(f"{what} '{name}' must be snake_case (a-z, 0-9, _) and start with a letter")


def header() -> str:
    lines = (ROOT / "header.txt").read_text(encoding="utf-8").splitlines()
    return "".join(f"# {line}\n" for line in lines if line.strip())


def render(template: pathlib.Path, **values: str) -> str:
    return string.Template(template.read_text(encoding="utf-8")).substitute(header=header(), **values)


def loc(text: str) -> int:
    """Non-blank lines."""
    return sum(1 for line in text.splitlines() if line.strip())


def add_import(init_py: pathlib.Path, module: str, dry_run: bool) -> bool:
    """Append `from . import <module>` to a package __init__.py, keeping its line endings."""
    line = f"from . import {module}"
    if not init_py.exists():
        if not dry_run:
            init_py.write_text(header() + "\n" + line + "\n", encoding="utf-8")
        return True
    data = init_py.read_bytes()
    text = data.decode("utf-8")
    if re.search(rf"^{re.escape(line)}\s*$", text, re.M):
        return False
    eol = "\r\n" if "\r\n" in text else "\n"
    if text and not text.endswith(("\n", "\r")):
        text += eol
    if not dry_run:
        init_py.write_bytes((text + line + eol).encode("utf-8"))
    return True


class Plan:
    """Collects files to write so the summary (files / LOC) can be printed and dry-run supported."""

    def __init__(self, dry_run: bool):
        self.dry_run = dry_run
        self.created: list[tuple[pathlib.Path, str]] = []
        self.edited: list[tuple[pathlib.Path, int]] = []

    def create(self, path: pathlib.Path, text: str) -> None:
        self.created.append((path, text))
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def edit(self, path: pathlib.Path, added_lines: int) -> None:
        self.edited.append((path, added_lines))

    def summary(self) -> None:
        verb = "would create" if self.dry_run else "created"
        total = 0
        for path, text in self.created:
            total += loc(text)
            print(f"  {verb} {path.relative_to(ROOT)}  ({loc(text)} lines)")
        for path, added in self.edited:
            total += added
            print(f"  {'would edit' if self.dry_run else 'edited'}  {path.relative_to(ROOT)}  (+{added} lines)")
        print(f"  => {len(self.created)} new files, {len(self.edited)} registrations, {total} non-blank lines generated")
