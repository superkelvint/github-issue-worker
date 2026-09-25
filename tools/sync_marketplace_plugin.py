#!/usr/bin/env python3
"""Keep the ChatGPT plugin skill mirror identical to root-level skills."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_SKILLS = ROOT / "plugins" / "github-coding-agent-skills" / "skills"
IGNORED_NAMES = {"__pycache__", ".DS_Store"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}
SHARED_CONTROL_PLANE = ROOT / "tools" / "control_plane_policy.py"
SHARED_CONTROL_PLANE_TARGETS = ("ci-fixer", "issue", "issue-fixer", "issue-followup", "pr-auto")


def discover_skills() -> list[Path]:
    skills: list[Path] = []
    for path in ROOT.iterdir():
        if not path.is_dir() or path.name.startswith("."):
            continue
        if path.name in {"plugins", "tools"}:
            continue
        if (path / "SKILL.md").is_file():
            skills.append(path)
    return sorted(skills, key=lambda path: path.name)


def included_files(root: Path) -> dict[Path, bytes]:
    files: dict[Path, bytes] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in IGNORED_NAMES for part in rel.parts):
            continue
        if path.suffix in IGNORED_SUFFIXES:
            continue
        files[rel] = path.read_bytes()
    return files


def copy_skill(source: Path, destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {
            name
            for name in names
            if name in IGNORED_NAMES or Path(name).suffix in IGNORED_SUFFIXES
        }

    shutil.copytree(source, destination, ignore=ignore)


def sync_control_plane_copies() -> None:
    content = SHARED_CONTROL_PLANE.read_bytes()
    for skill_name in SHARED_CONTROL_PLANE_TARGETS:
        target = ROOT / skill_name / "scripts" / "control_plane_policy.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def check_control_plane_copies() -> bool:
    expected = SHARED_CONTROL_PLANE.read_bytes()
    ok = True
    for skill_name in SHARED_CONTROL_PLANE_TARGETS:
        target = ROOT / skill_name / "scripts" / "control_plane_policy.py"
        if not target.is_file() or target.read_bytes() != expected:
            print(
                f"shared control-plane drift: {target.relative_to(ROOT)}",
                file=sys.stderr,
            )
            ok = False
    return ok


def sync() -> None:
    sync_control_plane_copies()
    skills = discover_skills()
    if PLUGIN_SKILLS.exists():
        shutil.rmtree(PLUGIN_SKILLS)
    PLUGIN_SKILLS.mkdir(parents=True, exist_ok=True)
    for source in skills:
        copy_skill(source, PLUGIN_SKILLS / source.name)


def check() -> bool:
    skills = discover_skills()
    expected_names = [path.name for path in skills]
    actual_names = sorted(
        path.name
        for path in PLUGIN_SKILLS.iterdir()
        if path.is_dir()
    ) if PLUGIN_SKILLS.is_dir() else []

    ok = check_control_plane_copies() and expected_names == actual_names
    if not ok:
        print(
            "marketplace skill set drift: "
            f"expected {expected_names}, found {actual_names}",
            file=sys.stderr,
        )

    for source in skills:
        mirrored = PLUGIN_SKILLS / source.name
        if not mirrored.is_dir():
            continue
        source_files = included_files(source)
        mirrored_files = included_files(mirrored)
        if source_files != mirrored_files:
            ok = False
            source_paths = set(source_files)
            mirrored_paths = set(mirrored_files)
            for path in sorted(source_paths - mirrored_paths):
                print(f"missing from marketplace mirror: {source.name}/{path}", file=sys.stderr)
            for path in sorted(mirrored_paths - source_paths):
                print(f"unexpected in marketplace mirror: {source.name}/{path}", file=sys.stderr)
            for path in sorted(source_paths & mirrored_paths):
                if source_files[path] != mirrored_files[path]:
                    print(f"content drift: {source.name}/{path}", file=sys.stderr)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed plugin mirror differs from root-level skills",
    )
    args = parser.parse_args()

    if args.check:
        if check():
            print("ChatGPT marketplace skill mirror is current")
            return 0
        print(
            "Run: python3 tools/sync_marketplace_plugin.py",
            file=sys.stderr,
        )
        return 1

    sync()
    if not check():
        print("failed to produce a current marketplace mirror", file=sys.stderr)
        return 1
    print(f"Synced {len(discover_skills())} skills into {PLUGIN_SKILLS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
