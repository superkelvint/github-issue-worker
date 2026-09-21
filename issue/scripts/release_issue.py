#!/usr/bin/env python3
"""Safely release an abandoned GitHub issue claim."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any

GH = os.environ.get("GH_BIN", "gh")


class CommandError(RuntimeError):
    def __init__(self, proc: subprocess.CompletedProcess[str]):
        super().__init__(proc.stderr.strip() or proc.stdout.strip() or "command failed")
        self.returncode = proc.returncode


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise CommandError(proc)
    return proc


def gh(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run([GH, *args], check=check)


def gh_json(*args: str) -> Any:
    proc = gh(*args)
    return json.loads(proc.stdout)


def infer_repo() -> str:
    repo = gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner").stdout.strip()
    if not repo:
        raise RuntimeError("could not infer GitHub repository")
    return repo


def get_login() -> str:
    return gh("api", "user", "--jq", ".login").stdout.strip()


def get_default_branch(repo: str) -> str:
    return gh(
        "repo", "view", repo, "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--repo")
    parser.add_argument("--branch-prefix", default="codex/issue")
    parser.add_argument("--label", default="in-progress")
    parser.add_argument("--reason", required=True)
    parser.add_argument("--next-step", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    repo = args.repo or infer_repo()
    login = get_login()
    branch = f"{args.branch_prefix}-{args.issue}"
    default_branch = get_default_branch(repo)

    prs = gh_json(
        "pr", "list", "--repo", repo, "--head", branch, "--state", "open", "--json", "number,url"
    )
    if prs and not args.force:
        print(json.dumps({"released": False, "reason": "open_pr_exists", "prs": prs}, indent=2))
        return 20

    compare = gh(
        "api",
        f"repos/{repo}/compare/{default_branch}...{branch}",
        "--jq",
        ".ahead_by",
        check=False,
    )
    if compare.returncode == 0:
        try:
            ahead_by = int(compare.stdout.strip() or "0")
        except ValueError:
            ahead_by = 0
        if ahead_by > 0 and not args.force:
            print(
                json.dumps(
                    {
                        "released": False,
                        "reason": "claim_branch_has_commits",
                        "ahead_by": ahead_by,
                        "branch": branch,
                    },
                    indent=2,
                )
            )
            return 21

    body = (
        f"Releasing claim by @{login}.\n\n"
        f"**Reason:** {args.reason}\n\n"
        f"**Required next step:** {args.next_step}"
    )
    gh("issue", "comment", str(args.issue), "--repo", repo, "--body", body, check=False)

    delete = gh("api", "--method", "DELETE", f"repos/{repo}/git/refs/heads/{branch}", check=False)
    if delete.returncode != 0:
        print(delete.stderr.strip() or "failed to delete claim branch", file=sys.stderr)
        return delete.returncode or 1

    if login:
        gh(
            "issue",
            "edit",
            str(args.issue),
            "--repo",
            repo,
            "--remove-assignee",
            login,
            check=False,
        )

    if args.label:
        gh(
            "issue",
            "edit",
            str(args.issue),
            "--repo",
            repo,
            "--remove-label",
            args.label,
            check=False,
        )

    print(json.dumps({"released": True, "repo": repo, "issue": args.issue, "branch": branch}, indent=2))
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
