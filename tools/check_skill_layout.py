#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
EXPECTED_NAMES = {
    "ci-fixer",
    "coverage-risk",
    "cto-reflection",
    "issue",
    "issue-fixer",
    "issue-followup",
    "pr-auto",
    "pr-reconciliation",
    "test-gut-check",
    "test-gut-check-batch",
    "verify",
}
NAME_RE = re.compile(r"^name:\s*([^\s#]+)\s*$")


def skill_name(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        match = NAME_RE.match(line.strip())
        if match:
            return match.group(1)
    return None


def main() -> int:
    if not (ROOT / "plugin.json").is_file():
        print("missing root plugin.json", file=sys.stderr)
        return 1
    if not SKILLS_ROOT.is_dir():
        print("missing canonical skills/ directory", file=sys.stderr)
        return 1

    canonical = sorted(SKILLS_ROOT.glob("*/SKILL.md"))
    discovered = sorted(ROOT.rglob("SKILL.md"))
    canonical_set = {path.resolve() for path in canonical}
    extras = [path for path in discovered if path.resolve() not in canonical_set]

    ok = True
    if extras:
        ok = False
        for path in extras:
            print(
                f"duplicate/noncanonical skill entrypoint: {path.relative_to(ROOT)}",
                file=sys.stderr,
            )

    actual_names = {path.parent.name for path in canonical}
    if actual_names != EXPECTED_NAMES:
        ok = False
        print(
            "canonical skill set mismatch: "
            f"expected {sorted(EXPECTED_NAMES)}, found {sorted(actual_names)}",
            file=sys.stderr,
        )

    declared: dict[str, Path] = {}
    for path in canonical:
        name = skill_name(path)
        if name is None:
            ok = False
            print(
                f"missing frontmatter name: {path.relative_to(ROOT)}",
                file=sys.stderr,
            )
            continue
        if name != path.parent.name:
            ok = False
            print(
                f"skill name/path mismatch: {path.relative_to(ROOT)} declares {name!r}",
                file=sys.stderr,
            )
        if name in declared:
            ok = False
            print(
                f"duplicate skill name {name!r}: "
                f"{declared[name].relative_to(ROOT)} and {path.relative_to(ROOT)}",
                file=sys.stderr,
            )
        else:
            declared[name] = path

    if not ok:
        return 1

    print(
        f"skill layout PASS: {len(canonical)} canonical skills "
        "and no duplicate entrypoints"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
