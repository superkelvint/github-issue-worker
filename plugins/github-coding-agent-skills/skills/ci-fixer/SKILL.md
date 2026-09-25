---
name: ci-fixer
description: Diagnose, explain, repair, and verify broken CI, builds, and repository development commands with minimal conversational tool churn by batching evidence gathering through Code Mode. Use for failing PR checks, red workflow runs, flaky jobs, stale PR branches, local/default-branch failures such as ./dev doctor, ./dev check, or ./dev universe, runner/toolchain/container problems, unrelated CI fanout, generated-artifact drift, compiler/linker/native SDK failures, or requests such as "what is wrong with PR 584", "fix the CI", "why is main broken", "fix ./dev check", or "merge it once green". Includes SearchKernel-specific live workflow/AGENTS handling and CTO closure rules.
---

# CI Fixer

## Goal

Turn a CI/build/development-environment investigation that would normally require many serial repository and GitHub calls into a small number of batched evidence-gathering passes, then repair the root cause when authorized.

Prefer evidence over guesses. Do not repeatedly poll or fetch broad logs when a narrower query can answer the question.

## Core operating rule: batch connector calls

Use Code Mode (`functions.exec`) as the orchestration layer for GitHub connector calls.

- Put independent reads in one `Promise.all(...)` call.
- Emit only the fields needed for the next reasoning step.
- Do not make one assistant tool call per status, job, log, or file when they can be fetched together.
- Perform dependent reads in stages: metadata -> failed jobs -> relevant logs -> fix/verification.
- Fetch full logs only for failed/cancelled jobs that remain unexplained after job/step metadata.
- Never fetch every job log merely because a workflow is red.

If a needed GitHub action is not already obvious, inspect `ALL_TOOLS` inside `functions.exec` and select the exact matching action. Do not guess action names.

## Inputs

Accept any of:

- PR URL or PR number;
- workflow run URL or run ID;
- commit SHA;
- a named failing check/job;
- a failing local or default-branch command plus its error/log, including repository entry points such as `./dev doctor`, `./dev check`, or `./dev universe`;
- a compiler, linker, container, toolchain, native-SDK, cache, or generated-artifact failure observed outside GitHub Actions;
- a request to inspect failing open PRs in a repository.

For SearchKernel project conversations, a bare PR number defaults to `superkelvint/searchkernel` unless the conversation clearly identifies another repository.

If the target is inferable, start immediately. Ask only when the repository/target is genuinely ambiguous.

## Action mode

Infer the requested mode from the user's wording:

### Inspect

Examples: "what's wrong", "why is this red", "diagnose PR 584", "why does ./dev check fail on main".

Diagnose and report. Do not mutate repository state.

### Repair

Examples: "fix it", "get CI green", "move this PR forward", "fix ./dev universe on main".

Diagnose, repair the root cause when safe and supported, push/update the PR, and verify the exact new head. Do not merge unless the user also requested merge/closure or their request clearly means complete the integration.

### Closure

Examples: "fix and merge", "merge when green", "finish this PR".

Diagnose, repair, verify, merge when repository rules permit, then perform required post-merge reconciliation.

Do not convert an inspect-only request into writes.

## SearchKernel live authority

Before substantive SearchKernel CI repair, review, PR management, merge, or closure:

1. Fetch `WORKFLOW.md` from `main` of `superkelvint/searchkernel-cto-state`.
2. Fetch `AGENTS.md` from `main` of `superkelvint/searchkernel`.
3. Follow the current versions, not bundled memory or prior copies.
4. If the failure is environment/toolchain/linker/native-SDK/build-provenance related, fetch current `BUILDING.md` before deciding it is a product defect.
5. If issue state/taxonomy is being changed, consult the current CTO-state issue-label authority named by `WORKFLOW.md`.

Do these live reads in parallel when possible.

Repository rules override generic repair behavior below. If current rules require a worktree or another execution constraint that the available environment cannot satisfy, diagnose fully and report the concrete blocker rather than bypassing the rule.

## Local/default-branch failure workflow

When the failure is observed locally or on the repository default branch and no PR exists yet:

1. Establish the repository, exact current default-branch head, failing command, and first meaningful error. Reproduce when the available execution environment can faithfully run the repository command; otherwise treat the supplied log as evidence and identify the environment gap.
2. Read repository build/environment authority before mutating toolchains or product code. For SearchKernel, fetch current `WORKFLOW.md`, `AGENTS.md`, and `BUILDING.md` in the same early batch.
3. Classify the failure with the same failure taxonomy used for CI. Correlate it with current default history, build scripts, container/toolchain contracts, generated artifacts, caches, native SDK provenance, and recent infrastructure changes as applicable.
4. In Repair/Closure mode, follow the repository's durable work rules before code changes. For SearchKernel, when the live `AGENTS.md` requires a directly assigned non-trivial repair to have an issue, create that exact bounded issue with canonical labels, claim it safely, and use the required task branch/worktree rather than editing shared `main`.
5. Add a regression/test for deterministic product or tooling defects when repository policy requires it, observe the failure before the fix, implement the smallest root-cause repair, and rerun the exact originally failing command.
6. Run broader verification proportional to the repair. Open/update the required PR and bind all further evidence to its exact head.
7. In Closure mode, continue through review/merge/post-merge reconciliation. In Inspect mode, stop after an evidenced diagnosis and smallest repair direction.

Do not create a separate generic repair workflow merely because the failure began outside GitHub Actions. The same root-cause classification and false-green rules apply.

## Diagnostic workflow

### Stage 1 — Resolve PR and cheap topology

For a PR target, batch the independent cheap reads first:

- PR metadata (`head_sha`, `base`, `base_sha`, branch, mergeability, draft/state);
- changed filenames;
- repository metadata/settings if merge behavior matters;
- PR comments/reviews only when review state may explain the block.

Do not fetch the full diff yet unless diagnosis needs it.

After obtaining `head_sha`, batch:

- workflow runs associated with the exact head SHA;
- combined commit status/check information;
- comparison of current base branch (usually `main`) against the PR head to detect behind/diverged state.

For SearchKernel, also include the live authority reads described above in the earliest sensible batch.

### Stage 2 — Isolate failing runs/jobs

From the exact-head workflow runs/statuses:

1. Ignore successful/skipped jobs except when their absence proves selector/fanout behavior.
2. Identify failed, timed-out, action-required, or cancelled runs.
3. Batch-fetch jobs for all relevant failing runs.
4. Extract failed job IDs, names, conclusions, runner labels, and failed step names.
5. Prefer the earliest meaningful failing step over later cascading failures.

A failure after an earlier setup/build error is usually collateral. Report the root step, not every downstream red step.

### Stage 3 — Fetch only useful logs

Batch-fetch logs for the failed jobs whose cause is not already explicit.

Summarize each log into:

- first meaningful error;
- 10-30 lines of surrounding semantic context when necessary;
- command/step that emitted it;
- repeated signature count if recurrence matters;
- whether later errors are cascading noise.

Do not dump large raw logs to the user.

If one job clearly establishes the root cause shared by many matrix jobs, do not fetch duplicate logs unless needed to prove the scope.

### Stage 4 — Correlate with the PR and current main

Before blaming the PR code, ask:

- Is the PR behind current `main`?
- Does current `main` contain a plausible fix for the exact failure signature?
- Is the failing job unrelated to the files/language/subsystem changed by the PR?
- Did the failure occur during provisioning, toolchain setup, container startup, dependency acquisition, generation checks, or linking before affected product tests ran?
- Does the same failure appear across unrelated PRs/runners?
- Did only one rerun fail while identical attempts pass, suggesting a transient flake?
- Is CI executing a lane that repository selection policy says should not run for this change?

Fetch diffs/workflow files/current-main files only when one of these hypotheses requires them.

## Failure classification

Classify the primary cause as one of:

- `STALE_PR_OR_FIXED_ON_MAIN` — PR is behind and current main contains the relevant repair/policy change.
- `WORKFLOW_SELECTION_OR_FANOUT` — CI selected unrelated languages/subsystems or failed to select required ones.
- `RUNNER_TOOLCHAIN_OR_CONTAINER` — runner state, missing/corrupted toolchain, container/image mismatch, workspace contamination, permissions, disk, or provisioning.
- `GENERATED_ARTIFACT_DRIFT` — checked-in generated outputs/BFBS/stubs/fixtures disagree with sources or pinned generators.
- `BUILD_LINK_NATIVE_SDK` — linker, ABI, RPATH, native SDK closure, compiler flags, or native dependency provenance.
- `PRODUCT_REGRESSION` — changed code or semantics genuinely breaks a relevant test/verifier.
- `TEST_OR_HARNESS_DEFECT` — test/harness expectation or setup is wrong while product behavior is not.
- `TRANSIENT_FLAKE` — evidence supports nondeterministic infrastructure/test failure; use sparingly.
- `REVIEW_OR_POLICY_BLOCK` — approvals, mergeability, required-check policy, or unresolved review state rather than a test failure.
- `UNKNOWN_NEEDS_DEEPER_EVIDENCE` — insufficient evidence; do not invent a diagnosis.

For recurring SearchKernel signatures and anti-patterns, consult `references/searchkernel-patterns.md`.

## Repair decision tree

### Stale PR / fix already on main

Prefer bringing the PR branch up to current base using the repository-approved mechanism, then verify the new exact head. Do not reimplement a fix already landed on main.

### Workflow selection/fanout defect

Repair the trusted selector/workflow policy, not the individual unrelated language test. Add or update selector regression coverage when the repository has such tests. Preserve fail-closed behavior for genuinely unknown/required paths.

### Runner/toolchain/container defect

Repair provisioning or runner isolation rather than product code. For SearchKernel, follow current `BUILDING.md`; do not improvise destructive cleanup that repository guidance forbids.

### Generated artifact drift

Regenerate only through the repository's authoritative generator/toolchain. Never hand-edit generated artifacts to make checks green.

### Build/link/native SDK defect

Treat compiler/linker/ABI/SDK provenance as its own domain. Verify pinned versions and runtime dependency closure. Do not mask failures with broad linker flags, ad-hoc library copies, or environment-specific paths unless current repository guidance explicitly requires them.

### Product regression

For SearchKernel and any repository that requires regression-test-first:

1. add/reproduce the failing regression first;
2. observe it fail before the production fix;
3. implement the smallest correct fix;
4. rerun the focused regression;
5. run the broader verification required by blast radius.

Do not weaken existing tests merely to pass.

### Test/harness defect

Prove why the expectation/setup is wrong before changing it. Ensure the revised test still fails for the bug it is intended to catch.

### Transient flake

A single targeted rerun is reasonable only when evidence supports flakiness or transient infrastructure. Do not enter a rerun-until-green loop. If it fails again, reclassify and investigate.

## Making changes

When repair mode authorizes mutation:

- Follow the repository's current branching/worktree/write rules.
- Make the smallest coherent change that repairs the root cause.
- Avoid unrelated cleanup.
- Preserve architecture and frozen contracts.
- Update durable documentation when the repair reveals a non-obvious recurring invariant and repository rules call for it.
- Push/update the existing PR when working on that PR; do not create duplicate repair PRs unnecessarily.

If only GitHub connector writes are available but current repository rules require a local worktree or other unavailable mechanism, stop at a fully evidenced diagnosis and concrete patch plan rather than violating the rules.

## Verification after repair

Never infer success from a write operation.

1. Re-fetch PR metadata and record the new exact `head_sha`.
2. Verify the expected commit is reachable on that head.
3. Fetch workflow runs/statuses for that exact head, not the old one.
4. Run/fetch focused verification appropriate to the fix.
5. For SearchKernel correctness-sensitive changes, apply the current `WORKFLOW.md` definition of done, including adversarial falsification and exact-head verification.
6. If native behavior is in blast radius, do not treat ordinary GitHub CI as proof of native behavior when current `AGENTS.md` says native verification is agent-local.

A green run attached to an earlier head does not verify the repaired PR.

## Merge and closure

Only merge in Closure mode and only when current repository rules permit it.

Before merge:

- re-fetch PR info;
- confirm exact head has not moved unexpectedly;
- confirm required checks/verification are green or otherwise satisfied by current policy;
- confirm relevant review comments/blockers are resolved;
- perform the required final/adversarial review for the change's blast radius;
- use expected-head protection when the GitHub merge action supports it.

For SearchKernel, after a substantive merge, follow the current CTO workflow all the way through post-merge reconciliation: current `main` head, applicable CI, issue/PR state, acceptance criteria, commit reachability, architectural invariants, and CTO control-plane state. Do not call work VERIFIED/CLOSED merely because GitHub reported `merged=true`.

## False-green challenge

Before declaring a repair complete, ask how the result could be falsely green. Check relevant items based on blast radius:

- stale workflow run attached to an old SHA;
- skipped/absent required lane;
- selector incorrectly excluding the changed subsystem;
- rerun masking deterministic failure;
- test never reaching the modified code path;
- generated files accepted while source is stale, or vice versa;
- local environment supplying an undeclared dependency;
- native path not exercised;
- error swallowed or converted into a successful fallback;
- matrix job marked optional when it should gate;
- branch updated after verification;
- merge succeeded while the issue/acceptance criteria remain unresolved.

## Output format

Keep the user-facing result compact and evidence-dense. Use this structure unless the situation calls for less:

**CI status:** `<GREEN | RED | REPAIRING | BLOCKED | MERGED>` — PR/run and exact head SHA.

**Root cause:** one or two sentences naming the classification and concrete failure.

**Evidence:** failed workflow/job/step, first meaningful error, and the key correlation to changed files/main/runner state.

**Action:** what was changed or rerun. If inspect-only, state the smallest recommended repair.

**Verification:** exact-head checks/results. Distinguish focused verification, broader CI, and native/local verification.

**Remaining:** only unresolved blockers or risks. Omit this section when none remain.

Do not give a giant inventory of successful checks unless the user asks.

## Example requests

- "What's wrong with PR 584?"
- "Fix the failing CI on #461."
- "This Ruby-only PR is running TypeScript and Python checks. Fix that."
- "Why did this workflow lose cargo halfway through?"
- "Why does ./dev doctor fail on main? Fix the root cause."
- "Fix ./dev universe; it is rebuilding the native/toolchain state incorrectly."
- "Bring all failing PRs up to the main CI fixes."
- "Fix and merge this once the exact head is green."

## Deterministic policy helper

Use `scripts/ci_fixer_policy.py` as the deterministic reference for failure classification, action-mode boundaries, selective log retrieval, one-shot transient reruns, bounded-repair authorization, exact-head verification, and closure-mode merge gating. It is a guardrail, not a substitute for repository-specific evidence.

After changing CI Fixer policy, run:

```bash
python3 -m unittest discover -s ci-fixer/scripts -p "test_*.py" -v
```
