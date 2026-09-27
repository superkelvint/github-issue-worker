#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_REL = Path("plugins/github-coding-agent-skills")
PLUGIN_ROOT = ROOT / PLUGIN_REL
SKILLS_ROOT = PLUGIN_ROOT / "skills"
PORTABLE_MANIFEST = PLUGIN_ROOT / "plugin.json"
COMPAT_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"
EXPECTED_MARKETPLACE_PATH = "./plugins/github-coding-agent-skills"
PLUGIN_NAME = "github-coding-agent-skills"
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
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
YAML_KEY_RE = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*?))?\s*$")
REQUIRED_INTERFACE_FIELDS = ("display_name", "short_description")


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, f"missing required JSON file: {path.relative_to(ROOT)}"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"invalid JSON in {path.relative_to(ROOT)}: {exc}"
    if not isinstance(value, dict):
        return None, f"JSON root must be an object: {path.relative_to(ROOT)}"
    return value, None


def skill_frontmatter(path: Path) -> dict[str, str] | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    result: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return result
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = YAML_KEY_RE.match(line)
        if match and not match.group(1):
            value = (match.group(3) or "").strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                value = value[1:-1]
            result[match.group(2)] = value
    return None


def validate_skill_frontmatter(path: Path) -> list[str]:
    frontmatter = skill_frontmatter(path)
    rel = path.as_posix()
    if frontmatter is None:
        return [f"invalid or unterminated YAML frontmatter: {rel}"]

    errors: list[str] = []
    name = frontmatter.get("name", "").strip()
    description = frontmatter.get("description", "").strip()

    if not name:
        errors.append(f"missing frontmatter name: {rel}")
    elif len(name) > 64 or not NAME_RE.fullmatch(name):
        errors.append(f"invalid skill name {name!r}: {rel}")

    if not description:
        errors.append(f"missing frontmatter description: {rel}")
    else:
        if len(description) > 1024:
            errors.append(f"skill description exceeds 1024 characters: {rel}")
        if "<" in description or ">" in description:
            errors.append(f"skill description contains forbidden angle brackets: {rel}")

    return errors


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

    errors: list[str] = []
    if interface_indent is None:
        return [f"missing interface mapping: {rel}"]

    for field in REQUIRED_INTERFACE_FIELDS:
        if not fields.get(field):
            errors.append(f"missing interface.{field}: {rel}")
    return errors


def validate_marketplace_data(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    plugins = data.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        return ["marketplace must contain exactly one plugin entry"]

    entry = plugins[0]
    if not isinstance(entry, dict):
        return ["marketplace plugin entry must be an object"]

    if entry.get("name") != PLUGIN_NAME:
        errors.append(f"marketplace plugin name must be {PLUGIN_NAME!r}")

    source = entry.get("source")
    if not isinstance(source, dict):
        errors.append("marketplace plugin source must be an object")
    else:
        if source.get("source") != "local":
            errors.append("marketplace plugin source.source must be 'local'")
        if source.get("path") != EXPECTED_MARKETPLACE_PATH:
            errors.append(
                "marketplace plugin source.path must be "
                f"{EXPECTED_MARKETPLACE_PATH!r}"
            )

    policy = entry.get("policy")
    if not isinstance(policy, dict):
        errors.append("marketplace plugin policy must be an object")
    else:
        if policy.get("installation") != "AVAILABLE":
            errors.append("marketplace installation policy must be 'AVAILABLE'")
        if policy.get("authentication") != "ON_INSTALL":
            errors.append("marketplace authentication policy must be 'ON_INSTALL'")

    if not entry.get("category"):
        errors.append("marketplace plugin category is required")
    return errors


def validate_manifests() -> list[str]:
    errors: list[str] = []

    portable, error = load_json(PORTABLE_MANIFEST)
    if error:
        errors.append(error)
        portable = None

    compat, error = load_json(COMPAT_MANIFEST)
    if error:
        errors.append(error)
        compat = None

    if portable is not None:
        if portable.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
            errors.append("portable plugin manifest has wrong or missing Agent Plugins schema")
        if portable.get("name") != PLUGIN_NAME:
            errors.append(f"portable plugin name must be {PLUGIN_NAME!r}")
        version = portable.get("version")
        if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
            errors.append("portable plugin version must be semantic versioning")
        description = portable.get("description")
        if not isinstance(description, str) or not description.strip():
            errors.append("portable plugin description is required")

    if compat is not None:
        if compat.get("name") != PLUGIN_NAME:
            errors.append(f"compatibility plugin name must be {PLUGIN_NAME!r}")
        version = compat.get("version")
        if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
            errors.append("compatibility plugin version must be semantic versioning")
        if portable is not None and compat.get("version") != portable.get("version"):
            errors.append("portable and compatibility plugin versions must match")
        if compat.get("skills") != "./skills/":
            errors.append("compatibility manifest skills must be './skills/'")
        interface = compat.get("interface")
        if not isinstance(interface, dict):
            errors.append("compatibility manifest interface must be an object")
        else:
            for field in ("displayName", "shortDescription"):
                value = interface.get(field)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"compatibility manifest interface.{field} is required")

    marketplace, error = load_json(MARKETPLACE)
    if error:
        errors.append(error)
    elif marketplace is not None:
        errors.extend(validate_marketplace_data(marketplace))

    return errors


def main() -> int:
    errors: list[str] = []

    if (ROOT / "plugin.json").exists():
        errors.append("noncanonical root plugin.json exists; manifest belongs under plugins/")
    if (ROOT / "skills").exists():
        errors.append("noncanonical root skills/ exists; skills belong under the plugin package")
    if not PLUGIN_ROOT.is_dir():
        errors.append(f"missing canonical plugin directory: {PLUGIN_REL}")

    errors.extend(validate_manifests())

    if not SKILLS_ROOT.is_dir():
        errors.append(f"missing canonical skills directory: {SKILLS_ROOT.relative_to(ROOT)}")
    else:
        canonical = sorted(SKILLS_ROOT.glob("*/SKILL.md"))
        discovered = sorted(ROOT.rglob("SKILL.md"))
        canonical_set = {path.resolve() for path in canonical}

        for path in discovered:
            if path.resolve() not in canonical_set:
                errors.append(
                    f"duplicate/noncanonical skill entrypoint: {path.relative_to(ROOT)}"
                )

        actual_names = {path.parent.name for path in canonical}
        if actual_names != EXPECTED_NAMES:
            errors.append(
                "canonical skill set mismatch: "
                f"expected {sorted(EXPECTED_NAMES)}, found {sorted(actual_names)}"
            )

        declared: dict[str, Path] = {}
        for path in canonical:
            rel = path.relative_to(ROOT)
            skill_errors = validate_skill_frontmatter(path)
            errors.extend(error.replace(path.as_posix(), rel.as_posix()) for error in skill_errors)

            frontmatter = skill_frontmatter(path) or {}
            name = frontmatter.get("name", "")
            if name and name != path.parent.name:
                errors.append(f"skill name/path mismatch: {rel} declares {name!r}")
            if name:
                if name in declared:
                    errors.append(
                        f"duplicate skill name {name!r}: "
                        f"{declared[name].relative_to(ROOT)} and {rel}"
                    )
                else:
                    declared[name] = path

            metadata = path.parent / "agents" / "openai.yaml"
            for error in validate_agent_metadata(metadata):
                errors.append(
                    error.replace(metadata.as_posix(), metadata.relative_to(ROOT).as_posix())
                )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        f"plugin layout PASS: {len(EXPECTED_NAMES)} canonical skills under "
        f"{PLUGIN_REL}, valid manifests/marketplace metadata, and no duplicate entrypoints"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
