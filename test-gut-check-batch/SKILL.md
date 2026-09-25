---
name: test-gut-check-batch
description: Audit test coverage across every open GitHub pull request in a repository as a batch job. Use when asked to gut-check all open PRs, audit the whole PR fleet for missing tests, determine which open PRs are under-tested, batch-review issue test coverage, or improve test coverage across pending PRs. Inventory concrete tests per PR, map them to linked issue acceptance criteria and blast radius, challenge false-green coverage, repair bounded gaps on writable PR branches, verify exact heads, and record SHA-bound dispositions without merging PRs.
---

# Batch Test Gut Check

Audit the complete open-PR fleet for test adequacy. Treat each PR independently, but optimize discovery and evidence gathering as one batch operation.

This skill is the fleet form of `$test-gut-check`. It must not reduce the review to CI status, changed test-file count, or line coverage.

## Objective

For every open PR:

1. identify the exact current head and linked issue/acceptance scope;
2. inventory tests added or changed by the PR;
3. identify important pre-existing tests that constrain the changed behavior;
4. map coverage to acceptance criteria, execution paths, and blast radius;
5. challenge how the suite could be falsely green;
6. decide whether coverage is sufficient;
7. rectify bounded missing coverage on the existing PR branch when safe;
8. fix any product bug exposed by a new regression test, regression-first;
9. verify the resulting exact head;
10. record a SHA-bound disposition and continue to the next PR.

Never stop the whole batch because one PR is blocked. Process the rest and report that PR separately.

## Live authority

Before substantive SearchKernel work, fetch the current `main` versions of:

- `superkelvint/searchkernel-cto-state/WORKFLOW.md`
- `superkelvint/searchkernel/AGENTS.md`
- `BUILDING.md` when test/build/native environment behavior matters

Follow current repository rules, not remembered copies.

For any repository, read repository-root and applicable subtree `AGENTS.md` files before editing or running repository-specific verification.

## GitHub access and batching

Prefer the runtime's authenticated GitHub connector. Fall back to authenticated `gh` when necessary. Never substitute unauthenticated public web requests for private repository operations.

Use Code Mode to batch independent GitHub reads:

- list all open PRs once;
- fetch cheap metadata, changed filenames, labels, linked issue clues, comments, and exact heads in parallel;
- fetch full diffs only for PRs that need auditing;
- fetch source/test files only for the affected paths;
- fetch CI logs only when needed to understand verification or a failed repair.

Do not make one conversational tool round trip for every metadata field of every PR.

## Scope: all open PRs

Include every open PR, draft or ready, unless repository rules explicitly exclude a class of PRs from review.

Classify each PR as one of:

```text
AUDIT
    substantive change requiring a test gut check

N/A
    docs/formatting/mechanical change where runtime test coverage is genuinely not applicable

ACTIVE
    head is moving or another worker is actively changing the branch; defer mutation but still report current evidence

BLOCKED
    required source, permissions, environment, or oracle is genuinely unavailable
```

Do not silently skip draft PRs, red PRs, or PRs without a linked issue.

When no linked issue exists, derive the acceptance scope from the PR body, changed behavior, contracts, and review comments. State that the PR has no linked issue rather than inventing one.

## Exact-head audit cache

Use a durable PR comment marker so repeated batch runs can skip unchanged heads:

```text
<!-- test-gut-check-batch -->
TEST GUT CHECK
head_sha: <40-char SHA>
disposition: SUFFICIENT | GAPS_RECTIFIED | GAPS_REMAIN | N/A | BLOCKED
scope: <linked issue or concise acceptance scope>
reviewed_at: <timestamp if available>
```

Below the marker include a concise summary of:

- tests added/changed;
- important pre-existing coverage;
- gaps found;
- rectification performed;
- verification commands/results;
- residual risk.

On a later batch run:

- if a current marker exists for the exact head with `SUFFICIENT`, `GAPS_RECTIFIED`, or `N/A`, skip re-auditing that PR unless the user explicitly requests a fresh pass;
- if the head moved, the old record is stale and must not be treated as current evidence;
- if the prior disposition was `GAPS_REMAIN` or `BLOCKED`, re-check whether the blocker/gap is now actionable.

Do not use a plain label as the sole cache because labels are not SHA-bound.

## Stage 1 — Build the fleet snapshot

For each open PR collect, where available:

- number, title, URL;
- draft/ready state;
- exact `head_sha` and base SHA;
- head repository/branch and whether it is writable;
- labels and author/ownership clues;
- linked issue(s);
- changed filenames;
- current CI/check summary;
- current or stale test-gut-check marker;
- mergeability only as context, not as a test-quality signal.

First decide which PRs are unchanged and already covered by a current exact-head marker. Skip their expensive audit work.

## Stage 2 — Build the test inventory per PR

For each PR that needs auditing, inspect the implementation diff and affected code.

Always separate:

### Tests added or changed by this PR

List concrete executable tests/scenarios/verifiers/fixtures materially changed by the PR. For each record:

- file path;
- test or scenario name;
- class: unit, integration, conformance, native/real-engine, E2E, property/state-machine, verifier, golden/fixture;
- behavior proved;
- whether it exercises the real affected path or a substitute/mock.

Do not count formatting-only fixture churn as coverage.

### Relevant pre-existing coverage

Search existing tests by affected operation, symbol, protocol field, error code, semantic path, native entry point, client method, persistence behavior, or result shape.

Include only tests whose assertions actually constrain the changed behavior.

### Required acceptance/verifier coverage

Identify repository-required acceptance commands and architectural verifiers that apply even when the PR did not modify them.

## Stage 3 — Coverage mapping

Map the inventory to:

- linked issue acceptance criteria or derived PR scope;
- changed implementation branches;
- architecture boundaries crossed;
- material failure modes implied by the blast radius.

Consider relevant dimensions rather than mechanically requiring all of them:

```text
primary success path
reported regression reproduction
negative / malformed input
boundary values, limits, overflow
absence vs present-empty semantics
stable error code/domain and diagnostics
alternate semantic ingress paths
direct/portable vs RPC/client equivalence
native/real-engine behavior vs mock-only coverage
persistence / close-reopen / historical compatibility
lifecycle / cleanup / failure injection
concurrency / races / forced interleavings
generated artifact drift/reproducibility
ordering / recursive result / projection fidelity
unsupported combinations / fail-closed behavior
oracle or upstream parity
cross-language client parity
```

For SearchKernel, explicitly consider semantic bypasses, silent fallback/dropping, native-vs-portable disagreement, persistence/reopen, result fidelity, and error-domain consistency when they touch the PR.

## Stage 4 — False-green challenge

Ask how the existing tests could pass while the implementation remains wrong.

Check relevant patterns:

- assertions prove only success/no panic;
- changed branch is never reached;
- mock/test double replaces the path under review;
- expected and actual values share the same buggy helper;
- regenerated fixtures come from the implementation instead of an independent expectation/oracle;
- source-text/grep assertions substitute for runtime behavior;
- one ingress is tested while another supported ingress bypasses the change;
- persistence change has no reopen/restart check;
- concurrency test is actually sequential;
- client test proves encoding but not canonical IR/server meaning;
- error test checks only human text, not stable machine-readable domain/code;
- broad suite is green without an issue-specific assertion;
- CI/test evidence belongs to an older SHA.

If a plausible false-green path exists, treat it as a coverage gap.

## Stage 5 — Decide and rectify

Use one of:

```text
SUFFICIENT
    acceptance and material risk surface are defended; no concrete missing test identified

GAPS_FOUND
    meaningful behavior is untested or current tests can plausibly be falsely green

N/A
    runtime coverage is genuinely not applicable

BLOCKED
    coverage cannot be determined or repaired because of a genuine external blocker
```

### If `SUFFICIENT`

Record the evidence and continue.

### If `GAPS_FOUND` and the branch is safely writable

Repair the current PR rather than merely reporting the gap:

1. record the exact starting head SHA;
2. create/use an isolated worktree at that head;
3. add or strengthen the smallest missing test;
4. if the test exposes a correctness defect, run it before the production fix and confirm the intended failure;
5. implement the smallest correct fix;
6. run focused and repository-required verification;
7. re-read the remote PR head before push;
8. push only if the remote head is unchanged and the push is fast-forward;
9. verify the new exact head;
10. re-run the gut check on the changed delta;
11. record `GAPS_RECTIFIED` only when the new head is adequately defended.

Never force-push.

### If `GAPS_FOUND` but remediation is too broad

Do not silently expand the PR into another project. Create or route a focused follow-up according to repository workflow and record `GAPS_REMAIN` with the exact missing tests/behavior.

### If branch is not writable

Do not create a replacement PR without repository/user authority. Record actionable `GAPS_REMAIN` evidence and continue the batch.

## Concurrency handling

Before any mutation and again before push/comment disposition:

- re-read the PR head SHA;
- if it changed, prior exact-head conclusions are stale;
- restart the audit from the new head once when practical;
- if the head continues moving, classify `ACTIVE`, do not race the other worker, and continue to the next PR.

A batch job must favor forward progress without trampling active work.

## Verification proportional to the path

Match verification to the claimed behavior:

- native/runtime change -> applicable real-engine/native verifier;
- persistence change -> close/reopen and compatibility checks;
- portable semantics -> canonical semantic tests plus alternate ingress equivalence;
- client facade -> request meaning plus response/error interpretation;
- generation change -> canonical regeneration/reproducibility check;
- lifecycle/concurrency -> targeted failure/interleaving test rather than ordinary happy-path tests.

Tie final evidence to the exact pushed head.

## Durable comment policy

Post or update a gut-check marker when:

- the PR was substantively audited;
- a prior stale marker needs a current-head replacement;
- gaps were rectified;
- gaps remain and need durable review evidence;
- coverage is `N/A` and explaining why avoids repeated future work.

Avoid duplicate comments for the same exact head and disposition. Prefer updating the durable record when the connector/repository workflow supports it; otherwise add one new exact-head record and let later runs select the newest matching marker.

Do not merge or approve PRs. This skill audits and repairs test coverage only.

## Batch completion

After processing all open PRs, re-fetch heads for any PRs mutated during the run and ensure each final disposition is tied to the current remote head.

Produce a compact fleet report:

```text
TEST GUT CHECK — <repo>

Audited: <count>
  #123 SUFFICIENT — <short evidence>
  #124 GAPS_RECTIFIED — added <test>; fixed <bug>

Already current: <count>
  #120 SUFFICIENT @ <sha>

N/A: <count>
  #125 docs-only

Gaps remaining: <count>
  #126 <specific missing behavior / follow-up>

Blocked/active: <count>
  #127 ACTIVE — head changed during audit
  #128 BLOCKED — <first concrete blocker>

Repairs pushed: <count>
  #124 <new head SHA>

Fleet coverage state: <all current / remaining gaps and why>
```

Do not dump every test name into the fleet summary when many PRs exist. Put detailed per-PR inventories in the durable PR comments and summarize the important coverage result in the final batch report.

## Completion rules

The batch job is complete only after:

- every open PR has been classified;
- every substantive PR needing an audit has either current exact-head coverage evidence or an explicit blocker/gap;
- bounded actionable gaps have been rectified where safe;
- newly exposed bugs were fixed regression-first;
- repaired heads were reverified;
- unchanged PRs with current SHA-bound evidence were not needlessly re-audited;
- the final report identifies every remaining gap, active PR, or blocker.

Green CI alone is never a sufficient test-coverage disposition.

## Deterministic policy helper

Use `scripts/batch_gut_check_policy.py` as the deterministic reference for exact-head marker parsing, current-vs-stale audit caching, ACTIVE/BLOCKED/N/A/AUDIT classification, safe mutation eligibility, and continuing the fleet after blocked PRs.

After changing batch gut-check policy, run:

```bash
python3 -m unittest discover -s test-gut-check-batch/scripts -p "test_*.py" -v
```
