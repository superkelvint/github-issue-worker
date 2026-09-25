#!/usr/bin/env python3
"""Safely release an abandoned canonical GitHub issue claim."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.parse
from typing import Any

GH = os.environ.get("GH_BIN", "gh")
IN_PROGRESS_LABEL = "status:in-progress"
ALLOWED_RELEASE = {"status:ready", "status:blocked", "status:needs-followup"}
STATUS_PREFIX = "status:"

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
    return json.loads(gh(*args).stdout)

def infer_repo() -> str:
    repo = gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner").stdout.strip()
    if not repo:
        raise RuntimeError("could not infer GitHub repository")
    return repo

def get_login() -> str:
    return gh("api", "user", "--jq", ".login").stdout.strip()

def get_default_branch(repo: str) -> str:
    return gh("repo", "view", repo, "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name").stdout.strip()

def branch_exists(repo: str, branch: str) -> bool:
    encoded = urllib.parse.quote(branch, safe="")
    return gh("api", f"repos/{repo}/git/ref/heads/{encoded}", check=False).returncode == 0

def status_labels(repo: str, issue_number: int) -> list[str]:
    issue = gh_json("issue", "view", str(issue_number), "--repo", repo, "--json", "labels")
    return sorted(
        item.get("name")
        for item in issue.get("labels", [])
        if isinstance(item, dict) and str(item.get("name", "")).startswith(STATUS_PREFIX)
    )

def transition_status(repo: str, issue_number: int, new: str) -> None:
    labels = status_labels(repo, issue_number)
    if labels != [IN_PROGRESS_LABEL]:
        raise RuntimeError(f"issue is not solely {IN_PROGRESS_LABEL}: {labels!r}")
    if gh("issue", "edit", str(issue_number), "--repo", repo, "--remove-label", IN_PROGRESS_LABEL, check=False).returncode != 0:
        raise RuntimeError("could not remove status:in-progress")
    add = gh("issue", "edit", str(issue_number), "--repo", repo, "--add-label", new, check=False)
    if add.returncode != 0:
        gh("issue", "edit", str(issue_number), "--repo", repo, "--add-label", IN_PROGRESS_LABEL, check=False)
        raise RuntimeError(f"could not add release status {new}")
    actual = status_labels(repo, issue_number)
    if actual != [new]:
        gh("issue", "edit", str(issue_number), "--repo", repo, "--remove-label", new, check=False)
        gh("issue", "edit", str(issue_number), "--repo", repo, "--add-label", IN_PROGRESS_LABEL, check=False)
        raise RuntimeError(f"release status verification failed: {actual!r}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--repo")
    parser.add_argument("--branch-prefix", default="codex/issue")
    parser.add_argument("--release-status", default="status:ready", choices=sorted(ALLOWED_RELEASE))
    parser.add_argument("--reason", required=True)
    parser.add_argument("--next-step", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    repo = args.repo or infer_repo()
    login = get_login()
    branch = f"{args.branch_prefix}-{args.issue}"
    default_branch = get_default_branch(repo)

    prs = gh_json("pr", "list", "--repo", repo, "--head", branch, "--state", "open", "--json", "number,url")
    if prs and not args.force:
        print(json.dumps({"released": False, "reason": "open_pr_exists", "prs": prs}, indent=2))
        return 20

    if branch_exists(repo, branch):
        compare = gh("api", f"repos/{repo}/compare/{default_branch}...{branch}", "--jq", ".ahead_by", check=False)
        if compare.returncode == 0:
            try:
                ahead_by = int(compare.stdout.strip() or "0")
            except ValueError:
                ahead_by = 0
            if ahead_by > 0 and not args.force:
                print(json.dumps({"released": False, "reason": "claim_branch_has_commits", "ahead_by": ahead_by, "branch": branch}, indent=2))
                return 21

    transition_status(repo, args.issue, args.release_status)

    if branch_exists(repo, branch):
        encoded = urllib.parse.quote(branch, safe="")
        delete = gh("api", "--method", "DELETE", f"repos/{repo}/git/refs/heads/{encoded}", check=False)
        if delete.returncode != 0 and branch_exists(repo, branch):
            # Restore the claim state if branch deletion failed, avoiding a false-ready issue.
            gh("issue", "edit", str(args.issue), "--repo", repo, "--remove-label", args.release_status, check=False)
            gh("issue", "edit", str(args.issue), "--repo", repo, "--add-label", IN_PROGRESS_LABEL, check=False)
            print(delete.stderr.strip() or "failed to delete claim branch", file=sys.stderr)
            return delete.returncode or 1

    if login:
        gh("issue", "edit", str(args.issue), "--repo", repo, "--remove-assignee", login, check=False)

    body = f"Releasing claim by @{login}.\n\n**Reason:** {args.reason}\n\n**Required next step:** {args.next_step}\n\n**New queue state:** {args.release_status}"
    gh("issue", "comment", str(args.issue), "--repo", repo, "--body", body, check=False)

    print(json.dumps({"released": True, "repo": repo, "issue": args.issue, "branch": branch, "status": args.release_status}, indent=2))
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
