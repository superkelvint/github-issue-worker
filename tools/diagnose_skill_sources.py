#!/usr/bin/env python3
"""Show duplicate skill registrations across common Codex skill/plugin roots."""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

HOME = Path.home()
ROOTS = [
    ("agents", HOME / ".agents" / "skills"),
    ("codex", HOME / ".codex" / "skills"),
    ("plugin-cache", HOME / ".codex" / "plugins" / "cache"),
]

NAME_RE = re.compile(r"^name:\s*(.+?)\s*$")
SHORT_DESCRIPTION_RE = re.compile(r'^\s*short_description:\s*["\']?(.*?)["\']?\s*$')


def iter_skill_files(root: Path):
    if not root.is_dir():
        return
    for directory, dirs, files in os.walk(root, followlinks=True):
        dirs[:] = [name for name in dirs if name != ".git" and name != "__pycache__"]
        for filename in files:
            if filename.lower() == "skill.md":
                yield Path(directory) / filename


def frontmatter_name(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return path.parent.name

    if not lines or lines[0].strip() != "---":
        return path.parent.name

    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = NAME_RE.match(line)
        if match:
            return match.group(1).strip().strip('"\'')
    return path.parent.name


def short_description(path: Path) -> str:
    metadata = path.parent / "agents" / "openai.yaml"
    try:
        lines = metadata.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""

    for line in lines:
        match = SHORT_DESCRIPTION_RE.match(line)
        if match:
            return match.group(1).strip()
    return ""


def main() -> int:
    grouped: dict[str, list[tuple[str, Path, Path, str]]] = defaultdict(list)

    for source, root in ROOTS:
        for path in iter_skill_files(root) or ():
            grouped[frontmatter_name(path)].append(
                (source, path, Path(os.path.realpath(path)), short_description(path))
            )

    if not grouped:
        print("No skills found in the standard local Codex roots.")
        return 0

    duplicate_count = 0
    for name in sorted(grouped):
        entries = grouped[name]
        if len(entries) < 2:
            continue

        duplicate_count += 1
        print(f"{name}: {len(entries)} registrations")
        for source, path, real_path, description in entries:
            print(f"  [{source}] {path}")
            if real_path != path:
                print(f"    -> {real_path}")
            if description:
                print(f"    {description}")
        print()

    if duplicate_count == 0:
        print("No duplicate skill names found across local skill roots and plugin cache.")
        return 0

    print(
        f"Found {duplicate_count} duplicate skill name(s). "
        "Use either the marketplace/plugin copy or the local skill copy, not both.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
