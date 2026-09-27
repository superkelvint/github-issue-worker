---
name: pr-reconciliation
description: Reconcile open GitHub pull requests with main by updating each PR branch to include the latest base branch wherever GitHub can do so cleanly. Use when the user asks to reconcile PRs, pull main into all open PRs, bring open PRs up to main, sync PR branches with main, or run a best-effort PR update sweep. Continue past conflicts and permission failures. Never resolve conflicts, retarget PRs, force-push, rewrite history, merge or close PRs, or stop the whole sweep because one PR cannot be updated.
---

# PR Reconciliation

Bring every eligible open PR branch up to date with `main` on a best-effort basis. Favor GitHub-side branch updates; do not check out or mutate local PR branches.

## Workflow

1. Resolve the repository.
   - Use an explicit `owner/repo` from the user when supplied.
   - Otherwise infer the repository from the current checkout with `gh repo view`.
   - If no repository can be determined, ask only for the repository.

2. Resolve the base branch.
   - Default to `main`.
   - Use another branch only when the user explicitly requests it.
   - Do not retarget PRs whose base differs from the requested base.

3. Reconcile all open PRs targeting that base, including drafts.
   - Run `scripts/reconcile-open-prs.sh` from this skill.
   - Pass `--repo owner/repo` when the repository is known explicitly.
   - Pass `--base <branch>` only when the requested base is not `main`.
   - Pass `--dry-run` only when the user asked for a preview.

4. Continue through individual failures.
   - Treat merge conflicts, fork restrictions, branch protection, permissions, stale races, and unsupported update operations as per-PR skips.
   - Do not attempt conflict resolution.
   - Do not rebase unless the user explicitly asks for a different skill/workflow.
   - Do not force-push or move refs directly.

5. Report a compact reconciliation summary.
   - State repository and base branch.
   - State how many PRs were discovered.
   - List PRs successfully reconciled.
   - List skipped PRs with the short reason reported by GitHub.
   - If no PRs needed or accepted an update, say so plainly.

## Safety invariants

- Never merge a pull request as part of reconciliation.
- Never close or reopen a pull request.
- Never change PR title, body, labels, reviewers, draft state, or base branch.
- Never resolve conflicts automatically.
- Never rewrite branch history.
- Never stop the sweep merely because one PR fails.
- Prefer the GitHub `update-branch` operation over local Git merges.

## Fallback when the bundled script cannot run

Use the available GitHub tooling directly with the same semantics:

1. Enumerate every open PR whose base is the requested base branch.
2. For each PR, invoke GitHub's native branch-update operation if available.
3. Process PRs independently; continue after any individual failure.
4. Do not substitute a PR merge operation, a force ref update, or manual conflict resolution.
5. Return the same reconciled/skipped summary.
