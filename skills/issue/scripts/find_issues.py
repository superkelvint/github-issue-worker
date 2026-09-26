#!/usr/bin/env python3
"""Find actionable unclaimed GitHub issues from the canonical ready queue."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any

GH = os.environ.get("GH_BIN", "gh")
READY_LABEL = "status:ready"
STATUS_PREFIX = "status:"
PRIORITIES = {
    "priority:p0": 0,
    "priority:p1": 1,
    "priority:p2": 2,
    "priority:p3": 3,
}


class CommandError(RuntimeError):
    def __init__(self, cmd: list[str], proc: subprocess.CompletedProcess[str]):
        super().__init__(proc.stderr.strip() or proc.stdout.strip() or "command failed")
        self.cmd = cmd
        self.returncode = proc.returncode


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise CommandError(args, proc)
    return proc


def gh(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run([GH, *args], check=check)


def gh_json(*args: str) -> Any:
    proc = gh(*args)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"gh returned invalid JSON: {proc.stdout!r}") from exc


def infer_repo() -> str:
    repo = gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner").stdout.strip()
    if not repo:
        raise RuntimeError("could not infer GitHub repository")
    return repo


def label_names(issue: dict[str, Any]) -> set[str]:
    return {
        str(item.get("name", ""))
        for item in issue.get("labels", [])
        if isinstance(item, dict) and item.get("name")
    }


def priority_rank(labels: set[str]) -> int:
    ranks = [rank for label, rank in PRIORITIES.items() if label in labels]
    return min(ranks) if ranks else len(PRIORITIES)


def created_rank(issue: dict[str, Any]) -> str:
    value = str(issue.get("createdAt") or "")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", help="owner/name; inferred from current checkout when omitted")
    parser.add_argument("--query", default="", help="optional hard keyword/label filter appended to ready queue")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    if args.limit <= 0 or args.limit > 100:
        raise RuntimeError("--limit must be between 1 and 100")

    repo = args.repo or infer_repo()
    search_parts = [f'label:"{READY_LABEL}"']
    if args.query.strip():
        search_parts.append(args.query.strip())
    search = " ".join(search_parts)

    issues = gh_json(
        "issue", "list",
        "--repo", repo,
        "--state", "open",
        "--search", search,
        "--limit", str(args.limit),
        "--json", "number,title,body,labels,assignees,url,createdAt,updatedAt",
    )

    eligible: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []

    for issue in issues:
        labels = label_names(issue)
        statuses = sorted(label for label in labels if label.startswith(STATUS_PREFIX))
        if statuses != [READY_LABEL]:
            invalid.append({
                "number": int(issue["number"]),
                "reason": "invalid_status_labels",
                "status_labels": statuses,
            })
            continue
        eligible.append(issue)

    eligible.sort(
        key=lambda issue: (
            priority_rank(label_names(issue)),
            created_rank(issue),
            int(issue["number"]),
        )
    )

    print(json.dumps({
        "repo": repo,
        "query": args.query,
        "ready_label": READY_LABEL,
        "eligible": eligible,
        "invalid": invalid,
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CommandError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(exc.returncode or 1)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
