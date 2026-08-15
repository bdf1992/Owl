#!/usr/bin/env python3
"""Report whether the installed skill matches this repository.

Editing the repo and then testing behavior against a stale installed copy
produces confident conclusions about the wrong creature. This makes the
active version visible before that happens.

Read-only: it never writes to the install path.

    python3 draw-the-owl/scripts/check_install.py [--install PATH]

Exit codes: 0 match, 1 differs, 2 not installed.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


REPO_SKILL = Path(__file__).resolve().parents[1]
DEFAULT_INSTALL = Path.home() / ".claude" / "skills" / "draw-the-owl"
SKIP_DIRS = {"tests", "__pycache__", ".git"}


def digest(path: Path) -> str:
    # Normalize line endings first. Git checks out CRLF on Windows while the
    # installed copy keeps LF, so a raw byte hash reports every file as stale
    # and the check becomes a light nobody reads.
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def tracked_files(root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if SKIP_DIRS.intersection(relative.parts):
            continue
        found[relative.as_posix()] = path
    return found


def compare(install: Path) -> tuple[list[str], list[str], list[str]]:
    """Return (missing, differing, extra) relative paths."""
    repo_files = tracked_files(REPO_SKILL)
    install_files = tracked_files(install)
    missing = [name for name in repo_files if name not in install_files]
    extra = [name for name in install_files if name not in repo_files]
    differing = [
        name
        for name, path in repo_files.items()
        if name in install_files and digest(path) != digest(install_files[name])
    ]
    return sorted(missing), sorted(differing), sorted(extra)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", type=Path, default=DEFAULT_INSTALL)
    arguments = parser.parse_args(argv)
    install = arguments.install

    if not install.is_dir():
        print(f"NOT INSTALLED  {install}")
        print("The repo copy is the only copy; nothing to fall out of date.")
        return 2

    missing, differing, extra = compare(install)
    if not (missing or differing or extra):
        print(f"MATCHES        {install}")
        return 0

    print(f"STALE          {install}")
    for name in differing:
        print(f"  differs      {name}")
    for name in missing:
        print(f"  absent       {name}")
    for name in extra:
        print(f"  not in repo  {name}")
    print()
    print("The active skill is not the skill in this repository.")
    print(f"Refresh it before testing behavior: copy {REPO_SKILL} over {install}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
