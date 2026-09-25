# GitHub Coding Agent Skills

This repository contains five independent Codex/ChatGPT skills for GitHub engineering workflows.

## $issue

Select one open issue, optionally filter by keyword, claim it atomically, implement it test-first, verify it, and open a PR.

Examples:

~~~text
$issue
$issue hnsw
$issue "schema fidelity"
~~~

Once $issue successfully claims an issue, it may not terminate with the issue stranded: it must either open/preserve an implementation PR or release the claim.

## $verify

Process all open PRs that are still in GitHub draft state. Verify the exact head, run repository-required tests/checks, repair PR-scoped failures when safe, push fixes to the existing branch, reverify, and mark the PR ready for review only when all required gates pass.

~~~text
$verify
~~~

$verify never merges or approves PRs. Non-draft PRs are outside its queue.

## $issue-followup

Process one open issue labeled `needs-followup`, claim it by moving the issue to `followup-in-progress`, update the existing PR/branch with the requested correction or missing verification, then hand it back by marking the PR ready and moving the issue to `needs-cto-review`.

~~~text
$issue-followup
~~~

$issue-followup does not merge, approve, close, or create replacement PRs for ordinary follow-up work.

## $ci-fixer

Diagnose broken GitHub Actions CI with batched GitHub reads, isolate the first meaningful failure, classify the root cause, repair it when authorized, and verify the exact repaired PR head. It understands stale branches, unrelated CI fanout, runner/toolchain/container failures, generated-artifact drift, build/link/native SDK failures, real product regressions, and test/harness defects.

~~~text
$ci-fixer PR 584
$ci-fixer fix CI on PR 461
$ci-fixer fix and merge PR 470
~~~

For SearchKernel, $ci-fixer fetches the current CTO workflow and repository agent rules before substantive repair or merge work and performs exact-head/false-green checks instead of treating a rerun or merge result as sufficient evidence.

## $pr-auto

Drive the open PR fleet to the furthest safe state it can reach: batch status discovery, update stale branches, fix bounded CI/code/conflict problems, review ready PRs, apply a blast-radius-aware CTO gut check for adversarial review, track that evidence by exact head SHA, merge eligible PRs, reconcile linked issues, then repeat until no additional safe action remains.

~~~text
$pr-auto
pr auto
$pr-auto status
$pr-auto 584
~~~

A bare `pr auto` is intentionally action-oriented. Use `pr auto status` for a read-only snapshot. PR Auto's deterministic policy helper is covered by `python3 pr-auto/scripts/test_pr_auto_policy.py`.

## Layout

~~~text
issue/
  SKILL.md
  agents/openai.yaml
  scripts/claim_issue.py
  scripts/release_issue.py
verify/
  SKILL.md
  agents/openai.yaml
issue-followup/
  SKILL.md
  agents/openai.yaml
ci-fixer/
  SKILL.md
  agents/openai.yaml
  references/searchkernel-patterns.md
pr-auto/
  SKILL.md
  agents/openai.yaml
  references/searchkernel.md
~~~

## GitHub access fallback

The skills prefer a runtime-native GitHub connector when it is actually exposed and sufficient. If that connector is missing or cannot perform the required authenticated repository operation, they fall back to authenticated `gh` — including inside ChatGPT/Codex runtimes. They must not substitute public web search or unauthenticated `curl` calls for private GitHub access.

## Local install

The simplest installation is to clone this repository directly as your Codex user skills directory:

~~~bash
git clone https://github.com/superkelvint/github-issue-worker.git ~/.agents/skills
~~~

That produces the discovery layout directly:

~~~text
~/.agents/skills/
  issue/SKILL.md
  verify/SKILL.md
  issue-followup/SKILL.md
  ci-fixer/SKILL.md
  pr-auto/SKILL.md
~~~

Then restart Codex if the skills do not appear immediately.

Update all five skills later with:

~~~bash
git -C ~/.agents/skills pull
~~~

### If `~/.agents/skills` already contains other skills

Do not clone over an existing non-empty directory. In that case, keep this repository elsewhere and symlink its five skill directories:

~~~bash
git clone https://github.com/superkelvint/github-issue-worker.git ~/.codex/github-issue-worker
ln -s ~/.codex/github-issue-worker/issue ~/.agents/skills/issue
ln -s ~/.codex/github-issue-worker/verify ~/.agents/skills/verify
ln -s ~/.codex/github-issue-worker/issue-followup ~/.agents/skills/issue-followup
ln -s ~/.codex/github-issue-worker/ci-fixer ~/.agents/skills/ci-fixer\nln -s ~/.codex/github-issue-worker/pr-auto ~/.agents/skills/pr-auto
~~~

If you previously installed an older copy of any of these skills, remove that old copy or symlink first so Codex does not discover duplicate skill names.
