---
name: coverage-risk
description: Analyze fresh repository code-coverage evidence, identify the highest-risk inadequately tested production areas, and reduce risk by adding or strengthening behavioral tests in descending risk order. Use when asked to inspect current coverage, find dangerous coverage gaps, improve coverage intelligently, lower test risk, or run $coverage-risk. Prefer architectural and correctness risk over raw percentage gains; verify the exact repository head, reject stale coverage, and never treat line coverage as proof that native, persistence, lifecycle, concurrency, error, or semantic-boundary behavior is correct.
---

# Coverage Risk Reducer

Use coverage as a map of what tests execute, not as a quality score. The goal is to reduce the probability and blast radius of undetected defects.

## Workflow

1. Read repository instructions before changing anything.
   - Read the applicable `AGENTS.md` and delegated build/test docs.
   - For SearchKernel, fetch the current CTO `WORKFLOW.md` and repository `AGENTS.md` before substantive work.
   - Record the exact current HEAD.
2. Obtain coverage for that exact HEAD.
   - Prefer the repository's canonical coverage entry point. In SearchKernel, run `./dev coverage`.
   - A previously generated report is reusable only when its metadata names the exact current HEAD, records a clean worktree, and the test configuration is still applicable.
   - A freshly generated report from a dirty worktree is valid evidence for that current snapshot, but it must not be reused later as pristine exact-head evidence.
   - Do not install or mutate shared toolchains ad hoc when the repository defines an immutable build environment.
3. Inventory coverage gaps.
   - Run `scripts/coverage_risk.py <summary.json> --root <repo-root>` when the report is cargo-llvm-cov JSON.
   - Use the output as a coverage-pressure inventory, not as a risk ranking.
   - Inspect the full JSON or HTML report to find concrete uncovered functions/regions for promising targets.
4. Rank by engineering risk, not by easiest percentage gain.
5. Take one bounded high-risk target at a time.
6. Add or strengthen behavioral tests that exercise meaningful behavior and assertions.
7. Re-run the focused test and coverage. Prove the intended production path is now executed and asserted.
8. Run repository-required broader verification for the blast radius.
9. Repeat in descending risk order until no meaningful high/medium-risk gap remains in the authorized scope, or a concrete blocker requires handoff.

## Risk ranking

Assess each candidate using evidence from code, architecture, contracts, git history, and the coverage report. Prefer qualitative `HIGH`, `MEDIUM`, `LOW` tiers with a short rationale over a single pseudo-precise number.

Raise risk for:

- lifecycle, ownership, concurrency, race, shutdown, reopen, or recovery behavior;
- persistence and compatibility paths;
- serialization, protocol verification, FFI/native, RPC, or process boundaries;
- canonical semantic conversion, normalization, validation, and alternate ingress paths;
- error-domain translation and fail-open/fail-closed behavior;
- malformed, boundary, overflow, absent-vs-present-empty, Unicode, large/truncated, or unsupported inputs;
- code with broad fan-out or architectural centrality;
- recent churn or a history of regressions;
- complex branches/state machines with weak or mock-only tests;
- uncovered code that guards destructive or irreversible behavior.

Lower priority for generated code, vendored/upstream code, trivial accessors, diagnostic-only paths, and mechanically repetitive glue when stronger tests already prove the governing invariant.

For SearchKernel, read `references/searchkernel.md` before ranking.

## False-green challenge

Before calling an area well covered, ask how the report could be green while the behavior is wrong. Check for all applicable failure modes:

- the test executes lines but never asserts the relevant outcome;
- setup or helper execution inflates coverage without exercising the decision branch;
- only a mock/scripted backend is covered where the contract requires real Vespa;
- one semantic ingress path is covered while an equivalent path bypasses or diverges;
- success paths are covered but malformed/error/absence/boundary paths are not;
- lifecycle coverage omits close/reopen, failure during transition, or interleavings;
- persistence coverage omits reopen or historical-format compatibility;
- feature-flag combinations leave production code unmeasured;
- generated or test code dominates the denominator;
- the coverage artifact came from a different commit;
- line coverage hides branch/state-machine gaps;
- Rust coverage is mistaken for coverage of linked C/C++ native behavior.

Do not declare `VERIFIED` merely because coverage increased.

## Test quality rules

Add tests that defend behavior or invariants. Avoid tests whose only purpose is executing lines.

A useful test should normally contain:

- a meaningful input or state transition;
- an observable expected result or error;
- assertions that would fail if the targeted behavior regressed;
- the real semantic path required by the contract at the appropriate test level.

For a discovered product defect, follow regression-test-first discipline: write and observe the failing reproduction before changing production code, then fix and re-run it.

Do not weaken existing assertions, acceptance artifacts, or verifier requirements to gain coverage.

## Mutation and handoff

When authorized to improve coverage, make concrete changes rather than returning only a report.

- Work on a dedicated task branch/worktree when repository rules require it.
- Preserve unrelated work.
- Keep each remediation bounded to the selected risk area.
- If testing reveals a product bug, fix it only when safely within scope; otherwise file/report the defect with reproduction evidence.
- Commit and push verified changes and open/update a PR when repository workflow requires it.
- Do not merge, approve, or call work closed unless the governing repository/user instructions authorize that action.

## Completion report

Report:

- exact analyzed HEAD and worktree cleanliness/source state;
- coverage command/artifact used and freshness evidence;
- baseline line/function/region coverage where available;
- high-risk gaps found, with concrete reasons;
- gaps remediated and tests added/strengthened;
- before/after coverage for the targeted files or functions when meaningful;
- focused and broader verification commands/results;
- remaining high/medium risks, especially anything not measurable by the coverage tool.

Do not celebrate a global percentage increase when the remaining risk is concentrated in critical code.
