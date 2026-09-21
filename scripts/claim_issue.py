#!/usr/bin/env python3
"""Atomically claim one GitHub issue using a remote branch as the mutex."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
from typing import Any

GH = os.environ.get("GH_BIN", "gh")


class CommandError(RuntimeError):
    def __init__(self, cmd: list[str], proc: subprocess.CompletedProcess[str]):
        super().__init__(proc.stderr.strip() or proc.stdout.strip() or "command failed")
        self.cmd = cmd
        self.returncode = proc.returncode
        self.stdout = proc.stdout
        self.stderr = proc.stderr


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
    proc = gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner")
    repo = proc.stdout.strip()
    if not repo:
        raise RuntimeError("could not infer GitHub repository")
    return repo


def get_login() -> str:
    login = gh("api", "user", "--jq", ".login").stdout.strip()
    if not login:
        raise RuntimeError("could not determine authenticated GitHub login")
    return login


def get_default_branch(repo: str) -> str:
    branch = gh(
        "repo", "view", repo, "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"
    ).stdout.strip()
    if not branch:
        raise RuntimeError("repository has no default branch")
    return branch


def get_branch_head(repo: str, branch: str) -> str:
    encoded = urllib.parse.quote(branch, safe="")
    sha = gh("api", f"repos/{repo}/commits/{encoded}", "--jq", ".sha").stdout.strip()
    if not sha:
        raise RuntimeError(f"could not resolve head of {branch}")
    return sha


def remote_claim_exists(repo: str, branch: str) -> bool:
    endpoint = f"repos/{repo}/git/ref/heads/{branch}"
    return gh("api", endpoint, check=False).returncode == 0


def label_exists(repo: str, label: str) -> bool:
    data = gh_json("label", "list", "--repo", repo, "--limit", "100", "--json", "name")
    return any(item.get("name") == label for item in data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--repo", help="owner/name; inferred from current checkout when omitted")
    parser.add_argument("--branch-prefix", default="codex/issue")
    parser.add_argument("--label", default="in-progress")
    args = parser.parse_args()

    repo = args.repo or infer_repo()
    login = get_login()
    issue = gh_json(
        "issue",
        "view",
        str(args.issue),
        "--repo",
        repo,
        "--json",
        "state,title,assignees,url",
    )

    if issue.get("state") != "OPEN":
        print(json.dumps({"claimed": False, "reason": "issue_not_open", "issue": args.issue}))
        return 11

    other_assignees = [
        a.get("login")
        for a in issue.get("assignees", [])
        if a.get("login") and a.get("login") != login
    ]
    if other_assignees:
        print(
            json.dumps(
                {
                    "claimed": False,
                    "reason": "assigned_to_other_user",
                    "issue": args.issue,
                    "assignees": other_assignees,
                }
            )
        )
        return 12

    branch = f"{args.branch_prefix}-{args.issue}"
    default_branch = get_default_branch(repo)
    base_sha = get_branch_head(repo, default_branch)

    create = gh(
        "api",
        "--method",
        "POST",
        f"repos/{repo}/git/refs",
        "-f",
        f"ref=refs/heads/{branch}",
        "-f",
        f"sha={base_sha}",
        check=False,
    )
    if create.returncode != 0:
        if remote_claim_exists(repo, branch):
            print(
                json.dumps(
                    {
                        "claimed": False,
                        "reason": "claim_branch_exists",
                        "issue": args.issue,
                        "branch": branch,
                    }
                )
            )
            return 10
        raise CommandError([GH, "api", "POST", f"repos/{repo}/git/refs"], create)

    warnings: list[str] = []

    assign = gh(
        "issue", "edit", str(args.issue), "--repo", repo, "--add-assignee", login, check=False
    )
    if assign.returncode != 0:
        warnings.append("could_not_assign_issue")

    try:
        if args.label and label_exists(repo, args.label):
            add_label = gh(
                "issue", "edit", str(args.issue), "--repo", repo, "--add-label", args.label, check=False
            )
            if add_label.returncode != 0:
                warnings.append("could_not_add_label")
    except Exception:
        warnings.append("could_not_check_label")

    comment_body = (
        f"Claimed by @{login}. Canonical work branch: `{branch}`. "
        "The branch ref is the ownership lock; work will be submitted by PR."
    )
    comment = gh(
        "issue", "comment", str(args.issue), "--repo", repo, "--body", comment_body, check=False
    )
    if comment.returncode != 0:
        warnings.append("could_not_comment")

    print(
        json.dumps(
            {
                "claimed": True,
                "repo": repo,
                "issue": args.issue,
                "branch": branch,
                "base_branch": default_branch,
                "base_sha": base_sha,
                "login": login,
                "warnings": warnings,
            },
            indent=2,
        )
    )
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
