#!/usr/bin/env python3
"""Create or locate the dedicated worktree for a claimed GitHub issue branch."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


class CommandError(RuntimeError):
    def __init__(self, args: list[str], proc: subprocess.CompletedProcess[str]):
        super().__init__(proc.stderr.strip() or proc.stdout.strip() or "command failed")
        self.args_run = args
        self.returncode = proc.returncode


def run(args: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and proc.returncode != 0:
        raise CommandError(args, proc)
    return proc


def git(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], cwd=cwd, check=check)


def repo_root() -> Path:
    proc = git("rev-parse", "--show-toplevel")
    return Path(proc.stdout.strip()).resolve()


def parse_worktrees(root: Path) -> list[dict[str, str]]:
    proc = git("worktree", "list", "--porcelain", cwd=root)
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        entries.append(current)
    return entries


def local_branch_exists(root: Path, branch: str) -> bool:
    return git("show-ref", "--verify", "--quiet", f"refs/heads/{branch}", cwd=root, check=False).returncode == 0


def rev_parse(root: Path, ref: str) -> str:
    return git("rev-parse", ref, cwd=root).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, required=True)
    parser.add_argument("--branch-prefix", default="codex/issue")
    parser.add_argument("--path", help="Explicit worktree path; defaults to /tmp/<repo>-issue-<N>")
    parser.add_argument("--print-path", action="store_true")
    args = parser.parse_args()

    root = repo_root()
    branch = f"{args.branch_prefix}-{args.issue}"
    remote_ref = f"origin/{branch}"

    fetch = git("fetch", "origin", branch, cwd=root, check=False)
    if fetch.returncode != 0:
        raise RuntimeError(
            f"claimed remote branch {branch!r} is unavailable; claim the issue before creating its worktree"
        )

    remote_sha = rev_parse(root, remote_ref)
    worktrees = parse_worktrees(root)

    for entry in worktrees:
        entry_branch = entry.get("branch")
        if entry_branch != f"refs/heads/{branch}":
            continue
        path = Path(entry["worktree"]).resolve()
        if path == root:
            raise RuntimeError(
                f"{branch} is checked out in the current/shared checkout {root}; "
                "refusing to work there. Move that checkout off the issue branch, then retry."
            )
        head = rev_parse(path, "HEAD")
        if head != remote_sha:
            raise RuntimeError(
                f"existing worktree {path} for {branch} is at {head}, but {remote_ref} is {remote_sha}; "
                "refresh it deliberately before continuing"
            )
        if args.print_path:
            print(path)
        else:
            print(json.dumps({"worktree": str(path), "branch": branch, "head": head, "reused": True}, indent=2))
        return 0

    target = Path(args.path).expanduser().resolve() if args.path else Path("/tmp") / f"{root.name}-issue-{args.issue}"
    if target.exists():
        raise RuntimeError(
            f"worktree destination already exists but is not registered for {branch}: {target}; "
            "refusing to delete or reuse it"
        )

    if local_branch_exists(root, branch):
        local_sha = rev_parse(root, branch)
        if local_sha != remote_sha:
            raise RuntimeError(
                f"local branch {branch} is at {local_sha}, but {remote_ref} is {remote_sha}; "
                "refusing to attach a stale/diverged branch"
            )
        git("worktree", "add", str(target), branch, cwd=root)
    else:
        git("worktree", "add", "--track", "-b", branch, str(target), remote_ref, cwd=root)

    actual_branch = git("rev-parse", "--abbrev-ref", "HEAD", cwd=target).stdout.strip()
    head = rev_parse(target, "HEAD")
    if actual_branch != branch or head != remote_sha:
        raise RuntimeError(
            f"worktree verification failed: branch={actual_branch!r} head={head!r}, "
            f"expected branch={branch!r} head={remote_sha!r}"
        )

    if args.print_path:
        print(target)
    else:
        print(json.dumps({"worktree": str(target), "branch": branch, "head": head, "reused": False}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CommandError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
