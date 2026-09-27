#!/usr/bin/env python3
"""Summarize cargo-llvm-cov JSON into a production-file coverage pressure inventory.

This deliberately does not assign an engineering risk score. Architectural risk
requires repository context and judgment; this helper only makes the coverage
evidence deterministic and easy to inspect.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

DEFAULT_IGNORED_PARTS = {
    "target",
    "generated",
    "upstream",
    "vendor",
    "node_modules",
    ".git",
}
TEST_DIR_NAMES = {"test", "tests", "benches"}


def metric(summary: dict, name: str) -> tuple[int, int, float]:
    raw = summary.get(name) or {}
    count = int(raw.get("count") or 0)
    covered = int(raw.get("covered") or 0)
    percent = raw.get("percent")
    if percent is None:
        percent = (100.0 * covered / count) if count else 100.0
    return count, covered, float(percent)


def normalized_path(filename: str, root: Path | None) -> str:
    path = Path(filename)
    if root is not None:
        try:
            path = path.resolve().relative_to(root.resolve())
        except (OSError, ValueError):
            pass
    return path.as_posix()


def should_ignore(path: str, include_tests: bool) -> bool:
    parts = set(Path(path).parts)
    if parts & DEFAULT_IGNORED_PARTS:
        return True
    if not include_tests and parts & TEST_DIR_NAMES:
        return True
    return False


def load_files(payload: dict) -> list[dict]:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise ValueError("coverage JSON has no data[0] entry")
    files = data[0].get("files")
    if not isinstance(files, list):
        raise ValueError("coverage JSON has no data[0].files list")
    return files


def inventory(payload: dict, root: Path | None, include_tests: bool) -> list[dict]:
    out: list[dict] = []
    for item in load_files(payload):
        filename = item.get("filename")
        summary = item.get("summary")
        if not isinstance(filename, str) or not isinstance(summary, dict):
            continue
        path = normalized_path(filename, root)
        if should_ignore(path, include_tests):
            continue

        line_count, line_covered, line_percent = metric(summary, "lines")
        fn_count, fn_covered, fn_percent = metric(summary, "functions")
        region_count, region_covered, region_percent = metric(summary, "regions")
        uncovered_lines = max(0, line_count - line_covered)
        uncovered_functions = max(0, fn_count - fn_covered)
        uncovered_regions = max(0, region_count - region_covered)

        if line_count == 0 and fn_count == 0 and region_count == 0:
            continue

        out.append(
            {
                "path": path,
                "lines": {"count": line_count, "covered": line_covered, "percent": line_percent},
                "functions": {"count": fn_count, "covered": fn_covered, "percent": fn_percent},
                "regions": {"count": region_count, "covered": region_covered, "percent": region_percent},
                "uncovered_lines": uncovered_lines,
                "uncovered_functions": uncovered_functions,
                "uncovered_regions": uncovered_regions,
            }
        )

    # This is coverage pressure, not risk. Large uncovered production surfaces
    # appear early so the reviewer can combine them with architectural evidence.
    out.sort(
        key=lambda x: (
            -x["uncovered_lines"],
            -x["uncovered_functions"],
            x["lines"]["percent"],
            x["path"],
        )
    )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("coverage_json", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    try:
        payload = json.loads(args.coverage_json.read_text(encoding="utf-8"))
        rows = inventory(payload, args.root, args.include_tests)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"coverage-risk: {exc}", file=sys.stderr)
        return 2

    rows = rows[: max(0, args.limit)]
    if args.as_json:
        json.dump(rows, sys.stdout, indent=2, sort_keys=True)
        print()
        return 0

    print("Coverage pressure inventory (NOT an engineering-risk ranking)")
    print("uncovered  line%  fn%    region%  path")
    for row in rows:
        print(
            f"{row['uncovered_lines']:9d}  "
            f"{row['lines']['percent']:5.1f}  "
            f"{row['functions']['percent']:5.1f}  "
            f"{row['regions']['percent']:7.1f}  "
            f"{row['path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
