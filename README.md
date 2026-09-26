# GitHub Coding Agent Skills

This repository contains eleven independent Codex/ChatGPT skills for GitHub engineering workflows.

## $issue

Select one open issue, optionally filter by keyword, claim it atomically, implement it test-first, verify it, and open a PR.

Examples:

~~~text
$issue
$issue hnsw
$issue "schema fidelity"
~~~

Once $issue successfully claims an issue, it may not terminate with the issue stranded: it must either open/preserve an implementation PR or release the claim. Before handoff it also performs the same test-coverage gut check described below.

## $issue-fixer

Drive a specific or already-selected GitHub issue all the way from diagnosis to verified closure. It establishes the real issue/PR/CI state, reproduces defects test-first, implements the smallest correct repair, performs adversarial false-green review, runs a blast-radius-aware architecture audit when warranted, verifies the exact PR head, merges when repository policy permits, and reconciles post-merge state before calling the issue closed.

~~~text
$issue-fixer 461
fix issue 613 end to end
move #28 all the way to verified closure
~~~

Use `$issue` when the job is to discover/select/claim unspecified work and hand off a PR. Use `$issue-fixer` when a concrete issue is already identified and the requested endpoint is actual closure rather than PR handoff.

## $test-gut-check

Audit one issue or implementing PR for test quality. It reconstructs the implementation lineage, shows the concrete tests already defending the issue, maps them to acceptance criteria and blast radius, looks for false-green coverage, and then adds/strengthens missing tests. If a new regression exposes a product bug, it fixes that bug test-first and verifies the repaired exact head.

~~~text
$test-gut-check issue 584
determine test coverage for issue 496 and improve it
gut check the tests for PR 584
~~~

It works both before merge and when revisiting an already-merged issue.

## $test-gut-check-batch

Run the same coverage audit across a selectable PR fleet. Open PRs are the default, and a rolling closed-PR window such as `closed:72h` is also supported. It batches GitHub discovery, skips unchanged heads that already have a current SHA-bound audit record, audits substantive PRs, repairs bounded missing tests on writable PR branches, and continues past blocked/active PRs instead of stopping the whole run.

~~~text
$test-gut-check-batch
$test-gut-check-batch closed:72h
gut check test coverage on all open PRs
~~~

It never merges or approves PRs; its job is test inventory, gap detection, remediation, exact-head verification, and a compact fleet report.

## $coverage-risk

Measure fresh repository code coverage, identify inadequately tested production areas with the highest correctness/architectural risk, then improve behavioral coverage in descending risk order. It refuses to optimize blindly for percentage and explicitly challenges false-green cases such as mock-only coverage, stale artifacts, untested error/lifecycle paths, and Rust coverage being mistaken for native C++ coverage.

~~~text
$coverage-risk
analyze current repo coverage and fix the highest-risk gaps
improve coverage where it most reduces correctness risk
~~~

For SearchKernel it uses `./dev coverage` as the canonical exact-head evidence source and treats native/real-Vespa verification as separate required evidence when behavior crosses the native boundary.

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

Drive the open PR fleet to the furthest safe state it can reach: batch status discovery, update stale branches, fix bounded CI/code/conflict problems, review ready PRs, apply blast-radius-aware adversarial-review and architecture-audit gates, track both by exact head SHA, merge only after every required gate is current, reconcile linked issues, then repeat until no additional safe action remains.

~~~text
$pr-auto
pr auto
$pr-auto status
$pr-auto 584
~~~

A bare `pr auto` is intentionally action-oriented. Use `pr auto status` for a read-only snapshot. PR Auto's deterministic policy helper is covered by `python3 pr-auto/scripts/test_pr_auto_policy.py`.

## $pr-reconciliation

Bring every open PR targeting `main` up to the latest `main` wherever GitHub can do so cleanly. It uses GitHub's native branch-update operation, includes drafts, continues past conflicts and permission/fork restrictions, and reports what was updated versus skipped.

~~~text
$pr-reconciliation
reconcile all open PRs with main
pull main into every open PR where possible
~~~

It never resolves conflicts, rebases, force-pushes, retargets, merges, or closes PRs. One blocked PR never stops the rest of the sweep.

## $cto-reflection

Review recent SearchKernel/CTO conversations, normally the last 24 hours, and turn repeated friction into concrete process improvements. It refreshes the current CTO workflow and repository rules, inspects relevant skills, distinguishes tooling/workflow/skill/user-habit root causes, and challenges proposed shortcuts for false-green risk.

~~~text
$cto-reflection
cto reflection
reflect on the last 24 hours and improve our process
~~~

It prefers the narrowest durable fix: improve an existing skill when that is enough, create a new skill only when a distinct workflow is genuinely missing, and keep repository/tooling or CTO-policy changes as explicit recommendations unless authorized.

## Layout

The repository has one canonical skill tree. The same `skills/` directory is used by local Codex discovery and by the ChatGPT plugin package; there is no generated mirror.

~~~text
plugin.json
skills/
  issue/
    SKILL.md
    agents/openai.yaml
    scripts/
  issue-fixer/
    SKILL.md
    agents/openai.yaml
    references/
  test-gut-check/
  test-gut-check-batch/
  coverage-risk/
  verify/
  issue-followup/
  ci-fixer/
  pr-auto/
  pr-reconciliation/
  cto-reflection/
tools/
  check_skill_layout.py
~~~

CI rejects any second/noncanonical `SKILL.md` entrypoint inside the repository. Runtime duplicates can still occur if the same skills are enabled from both this local checkout and an installed marketplace plugin, so the installation modes below are intentionally mutually exclusive.

## GitHub access fallback

The skills prefer a runtime-native GitHub connector when it is actually exposed and sufficient. If that connector is missing or cannot perform the required authenticated repository operation, they fall back to authenticated `gh` — including inside ChatGPT/Codex runtimes. They must not substitute public web search or unauthenticated `curl` calls for private GitHub access.

## ChatGPT install (GitHub-synced)

This repository is also a ChatGPT plugin marketplace. The repository root is the plugin package and `skills/` is the single source of truth used by both the marketplace and local Codex discovery.

To connect it once as a workspace admin:

1. Open **Workspace settings > Plugins**.
2. Select **Add > Import marketplace**.
3. Use **Source** `https://github.com/superkelvint/github-issue-worker`.
4. Leave **Path** empty.
5. Use branch `main` (or leave Branch empty to follow the default branch).
6. Authorize GitHub and import the marketplace.

ChatGPT then checks the GitHub marketplace for updates daily. Use **Marketplaces > GitHub Coding Agent Skills > Sync now** when you want a merged skill change immediately.

When editing or adding a skill, change only `skills/<name>/`. Run `python3 tools/check_skill_layout.py` before committing; CI runs the same guard and rejects duplicate or noncanonical skill entrypoints.

## Local Codex install

Do **not** clone this entire repository into `~/.agents/skills`. This repository is also a plugin/marketplace package. Putting the plugin root inside a user skill-discovery directory can expose the same skill once as a local skill and again through the installed marketplace plugin.

Choose exactly one source for these eleven skills in a given Codex/ChatGPT profile.

### Option A: marketplace plugin

Use the marketplace/plugin installation described above and do not create local copies or symlinks for these same ten skills under `~/.agents/skills`.

### Option B: local-development skills

Use this when you want `git pull` to update the skills immediately while developing them. The marketplace plugin copy must not also be enabled in the same client/profile.

Clone the repository outside every skill-discovery directory:

~~~bash
git clone https://github.com/superkelvint/github-issue-worker.git ~/.codex/github-issue-worker
mkdir -p ~/.agents/skills
~~~

Then expose only the actual skill directories:

~~~bash
for skill in issue issue-fixer test-gut-check test-gut-check-batch coverage-risk verify issue-followup ci-fixer pr-auto pr-reconciliation cto-reflection; do
  ln -sfn "$HOME/.codex/github-issue-worker/skills/$skill" "$HOME/.agents/skills/$skill"
done
~~~

Update later with:

~~~bash
git -C ~/.codex/github-issue-worker pull
~~~

The repository root itself should never be a descendant of `~/.agents/skills`; only individual skill directories belong there.

### Migrating an existing clone safely

If this repository is currently cloned directly at `~/.agents/skills`, **move it; do not delete it**:

~~~bash
mv ~/.agents/skills ~/.codex/github-issue-worker
mkdir -p ~/.agents/skills
for skill in issue issue-fixer test-gut-check test-gut-check-batch coverage-risk verify issue-followup ci-fixer pr-auto pr-reconciliation cto-reflection; do
  ln -s "$HOME/.codex/github-issue-worker/skills/$skill" "$HOME/.agents/skills/$skill"
done
~~~

Before using local-development mode, make sure an installed/cached `github-coding-agent-skills` marketplace plugin is not also active in that same Codex/ChatGPT profile. Running both sources is expected to show duplicate skill names.

To diagnose where copies are coming from:

~~~bash
python3 ~/.codex/github-issue-worker/tools/diagnose_skill_sources.py
~~~

## Test all skills

The repository's deterministic skill helpers are covered with standard-library Python unit tests. Run the full suite with:

~~~bash
python3 tools/check_skill_layout.py
for dir in issue verify issue-followup ci-fixer pr-auto test-gut-check test-gut-check-batch coverage-risk cto-reflection; do
  python3 -m unittest discover -s "skills/$dir/scripts" -p 'test_*.py' -v
done
bash skills/pr-reconciliation/scripts/test-reconcile-open-prs.sh
~~~

The suite currently covers issue queue/claim/worktree/release safety, draft PR verification, follow-up lifecycle, CI diagnosis/repair policy, PR Auto fleet policy, PR reconciliation best-effort behavior, test gut-check policy, batch audit caching/mutation rules, coverage-risk inventory parsing, and CTO reflection recommendation guards.
