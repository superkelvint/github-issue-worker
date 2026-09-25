# GitHub Coding Agent Skills

This repository contains eight independent Codex/ChatGPT skills for GitHub engineering workflows.

## $issue

Select one open issue, optionally filter by keyword, claim it atomically, implement it test-first, verify it, and open a PR.

Examples:

~~~text
$issue
$issue hnsw
$issue "schema fidelity"
~~~

Once $issue successfully claims an issue, it may not terminate with the issue stranded: it must either open/preserve an implementation PR or release the claim. Before handoff it also performs the same test-coverage gut check described below.

## $test-gut-check

Audit one issue or implementing PR for test quality. It reconstructs the implementation lineage, shows the concrete tests already defending the issue, maps them to acceptance criteria and blast radius, looks for false-green coverage, and then adds/strengthens missing tests. If a new regression exposes a product bug, it fixes that bug test-first and verifies the repaired exact head.

~~~text
$test-gut-check issue 584
determine test coverage for issue 496 and improve it
gut check the tests for PR 584
~~~

It works both before merge and when revisiting an already-merged issue.

## $test-gut-check-batch

Run the same coverage audit across **every open PR** in one fleet pass. It batches GitHub discovery, skips unchanged heads that already have a current SHA-bound audit record, audits substantive PRs, repairs bounded missing tests on writable PR branches, and continues past blocked/active PRs instead of stopping the whole run.

~~~text
$test-gut-check-batch
gut check test coverage on all open PRs
audit every open PR for missing tests and fix what you can
~~~

It never merges or approves PRs; its job is test inventory, gap detection, remediation, exact-head verification, and a compact fleet report.

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

## $cto-reflection

Review recent SearchKernel/CTO conversations, normally the last 24 hours, and turn repeated friction into concrete process improvements. It refreshes the current CTO workflow and repository rules, inspects relevant skills, distinguishes tooling/workflow/skill/user-habit root causes, and challenges proposed shortcuts for false-green risk.

~~~text
$cto-reflection
cto reflection
reflect on the last 24 hours and improve our process
~~~

It prefers the narrowest durable fix: improve an existing skill when that is enough, create a new skill only when a distinct workflow is genuinely missing, and keep repository/tooling or CTO-policy changes as explicit recommendations unless authorized.

## Layout

~~~text
issue/
  SKILL.md
  agents/openai.yaml
  scripts/find_issues.py
  scripts/claim_issue.py
  scripts/create_worktree.py
  scripts/release_issue.py
  scripts/test_issue_helpers.py
test-gut-check/
  SKILL.md
  agents/openai.yaml
  scripts/gut_check_policy.py
  scripts/test_gut_check_policy.py
test-gut-check-batch/
  SKILL.md
  agents/openai.yaml
  scripts/batch_gut_check_policy.py
  scripts/test_batch_gut_check_policy.py
verify/
  SKILL.md
  agents/openai.yaml
  scripts/verify_policy.py
  scripts/test_verify_policy.py
issue-followup/
  SKILL.md
  agents/openai.yaml
  scripts/followup_policy.py
  scripts/test_followup_policy.py
ci-fixer/
  SKILL.md
  agents/openai.yaml
  scripts/ci_fixer_policy.py
  scripts/test_ci_fixer_policy.py
  references/searchkernel-patterns.md
pr-auto/
  SKILL.md
  agents/openai.yaml
  scripts/pr_auto_policy.py
  scripts/test_pr_auto_policy.py
  references/searchkernel.md
cto-reflection/
  SKILL.md
  agents/openai.yaml
  scripts/reflection_policy.py
  scripts/test_reflection_policy.py
  references/reflection-rubric.md
  references/report-template.md
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
  test-gut-check/SKILL.md
  test-gut-check-batch/SKILL.md
  verify/SKILL.md
  issue-followup/SKILL.md
  ci-fixer/SKILL.md
  pr-auto/SKILL.md
  cto-reflection/SKILL.md
~~~

Then restart Codex if the skills do not appear immediately.

Update all eight skills later with:

~~~bash
git -C ~/.agents/skills pull
~~~

### If `~/.agents/skills` already contains other skills

Do not clone over an existing non-empty directory. In that case, keep this repository elsewhere and symlink its eight skill directories:

~~~bash
git clone https://github.com/superkelvint/github-issue-worker.git ~/.codex/github-issue-worker
ln -s ~/.codex/github-issue-worker/issue ~/.agents/skills/issue
ln -s ~/.codex/github-issue-worker/test-gut-check ~/.agents/skills/test-gut-check
ln -s ~/.codex/github-issue-worker/test-gut-check-batch ~/.agents/skills/test-gut-check-batch
ln -s ~/.codex/github-issue-worker/verify ~/.agents/skills/verify
ln -s ~/.codex/github-issue-worker/issue-followup ~/.agents/skills/issue-followup
ln -s ~/.codex/github-issue-worker/ci-fixer ~/.agents/skills/ci-fixer
ln -s ~/.codex/github-issue-worker/pr-auto ~/.agents/skills/pr-auto
ln -s ~/.codex/github-issue-worker/cto-reflection ~/.agents/skills/cto-reflection
~~~

If you previously installed an older copy of any of these skills, remove that old copy or symlink first so Codex does not discover duplicate skill names.


## Test all skills

The repository's deterministic skill helpers are covered with standard-library Python unit tests. Run the full suite with:

~~~bash
for dir in issue verify issue-followup ci-fixer pr-auto test-gut-check test-gut-check-batch cto-reflection; do
  python3 -m unittest discover -s "$dir/scripts" -p 'test_*.py' -v
done
~~~

The suite currently covers issue queue/claim/worktree/release safety, draft PR verification, follow-up lifecycle, CI diagnosis/repair policy, PR Auto fleet policy, test gut-check policy, batch audit caching/mutation rules, and CTO reflection recommendation guards.
