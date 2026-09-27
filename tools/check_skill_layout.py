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
YAML_KEY_RE = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*?))?\s*$")
REQUIRED_INTERFACE_FIELDS = ("display_name", "short_description")


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


def _yaml_scalar(value: str | None) -> str:
    if value is None:
        return ""
    value = value.strip()
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    return value.strip()


def validate_agent_metadata(path: Path) -> list[str]:
    rel = path.as_posix()
    if not path.is_file():
        return [f"missing required agent metadata: {rel}"]

    fields: dict[str, str] = {}
    interface_indent: int | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        match = YAML_KEY_RE.match(raw_line)
        if not match:
            continue

        indent_text, key, value = match.groups()
        indent = len(indent_text.replace("\t", "    "))

        if interface_indent is None:
            if key == "interface" and not _yaml_scalar(value):
                interface_indent = indent
            continue

        if indent <= interface_indent:
            break

        if key in REQUIRED_INTERFACE_FIELDS:
            fields[key] = _yaml_scalar(value)

    errors = []
    if interface_indent is None:
        errors.append(f"missing interface mapping: {rel}")
        return errors

    for field in REQUIRED_INTERFACE_FIELDS:
        if not fields.get(field):
            errors.append(f"missing interface.{field}: {rel}")
    return errors


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

        metadata = path.parent / "agents" / "openai.yaml"
        for error in validate_agent_metadata(metadata):
            ok = False
            try:
                shown = metadata.relative_to(ROOT)
                error = error.replace(metadata.as_posix(), shown.as_posix())
            except ValueError:
                pass
            print(error, file=sys.stderr)

    if not ok:
        return 1

    print(
        f"skill layout PASS: {len(canonical)} canonical skills, "
        "required agent metadata present, and no duplicate entrypoints"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
