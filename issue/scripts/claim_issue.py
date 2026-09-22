#!/usr/bin/env python3
"""Atomically claim one canonical-ready GitHub issue."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
from typing import Any

GH = os.environ.get("GH_BIN", "gh")
READY_LABEL = "status:ready"
IN_PROGRESS_LABEL = "status:in-progress"
STATUS_PREFIX = "status:"

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
    return json.loads(gh(*args).stdout)

def infer_repo() -> str:
    repo = gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner").stdout.strip()
    if not repo:
        raise RuntimeError("could not infer GitHub repository")
    return repo

def get_login() -> str:
    login = gh("api", "user", "--jq", ".login").stdout.strip()
    if not login:
        raise RuntimeError("could not determine authenticated GitHub login")
    return login

def get_default_branch(repo: str) -> str:
    branch = gh("repo", "view", repo, "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name").stdout.strip()
    if not branch:
        raise RuntimeError("repository has no default branch")
    return branch

def get_branch_head(repo: str, branch: str) -> str:
    encoded = urllib.parse.quote(branch, safe="")
    sha = gh("api", f"repos/{repo}/commits/{encoded}", "--jq", ".sha").stdout.strip()
    if not sha:
        raise RuntimeError(f"could not resolve head of {branch}")
    return sha

def branch_exists(repo: str, branch: str) -> bool:
    encoded = urllib.parse.quote(branch, safe="")
    return gh("api", f"repos/{repo}/git/ref/heads/{encoded}", check=False).returncode == 0

def delete_branch(repo: str, branch: str) -> None:
    encoded = urllib.parse.quote(branch, safe="")
    proc = gh("api", "--method", "DELETE", f"repos/{repo}/git/refs/heads/{encoded}", check=False)
    if proc.returncode != 0 and branch_exists(repo, branch):
        raise RuntimeError(f"failed to roll back claim branch {branch}")

def status_labels(issue: dict[str, Any]) -> list[str]:
    return sorted(
        item.get("name")
        for item in issue.get("labels", [])
        if isinstance(item, dict) and str(item.get("name", "")).startswith(STATUS_PREFIX)
    )

def read_issue(repo: str, issue_number: int) -> dict[str, Any]:
    return gh_json("issue", "view", str(issue_number), "--repo", repo, "--json", "state,title,assignees,labels,url")

def set_status(repo: str, issue_number: int, old: str, new: str) -> None:
    remove = gh("issue", "edit", str(issue_number), "--repo", repo, "--remove-label", old, check=False)
    if remove.returncode != 0:
        raise RuntimeError(f"could not remove required status label {old}")
    add = gh("issue", "edit", str(issue_number), "--repo", repo, "--add-label", new, check=False)
    if add.returncode != 0:
        gh("issue", "edit", str(issue_number), "--repo", repo, "--add-label", old, check=False)
        raise RuntimeError(f"could not add required status label {new}")
    labels = status_labels(read_issue(repo, issue_number))
    if labels != [new]:
        gh("issue", "edit", str(issue_number), "--repo", repo, "--remove-label", new, check=False)
        gh("issue", "edit", str(issue_number), "--repo", repo, "--add-label", old, check=False)
        raise RuntimeError(f"status transition verification failed: {labels!r}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--repo")
    parser.add_argument("--branch-prefix", default="codex/issue")
    args = parser.parse_args()

    repo = args.repo or infer_repo()
    login = get_login()
    issue = read_issue(repo, args.issue)

    if issue.get("state") != "OPEN":
        print(json.dumps({"claimed": False, "reason": "issue_not_open", "issue": args.issue}))
        return 11

    labels = status_labels(issue)
    if labels != [READY_LABEL]:
        print(json.dumps({"claimed": False, "reason": "issue_not_ready", "issue": args.issue, "status_labels": labels}))
        return 13

    branch = f"{args.branch_prefix}-{args.issue}"
    default_branch = get_default_branch(repo)
    base_sha = get_branch_head(repo, default_branch)

    create = gh("api", "--method", "POST", f"repos/{repo}/git/refs", "-f", f"ref=refs/heads/{branch}", "-f", f"sha={base_sha}", check=False)
    if create.returncode != 0:
        if branch_exists(repo, branch):
            print(json.dumps({"claimed": False, "reason": "claim_branch_exists", "issue": args.issue, "branch": branch}))
            return 10
        raise CommandError([GH, "api", "POST", f"repos/{repo}/git/refs"], create)

    try:
        set_status(repo, args.issue, READY_LABEL, IN_PROGRESS_LABEL)
    except Exception:
        delete_branch(repo, branch)
        raise

    warnings: list[str] = []
    if gh("issue", "edit", str(args.issue), "--repo", repo, "--add-assignee", login, check=False).returncode != 0:
        warnings.append("could_not_assign_issue")
    body = f"Claimed by @{login}. Canonical work branch: codex/issue-{args.issue}."
    if gh("issue", "comment", str(args.issue), "--repo", repo, "--body", body, check=False).returncode != 0:
        warnings.append("could_not_comment")

    print(json.dumps({"claimed": True, "repo": repo, "issue": args.issue, "branch": branch, "base_branch": default_branch, "base_sha": base_sha, "status": IN_PROGRESS_LABEL, "login": login, "warnings": warnings}, indent=2))
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
