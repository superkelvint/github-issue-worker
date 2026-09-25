---
name: issue-fixer
description: Drive a specific or already-selected GitHub issue end-to-end from diagnosis to verified closure. Use when the user says to fix, resolve, finish, move forward, or close a named issue, or explicitly invokes the issue fixer and expects more than an issue-to-PR handoff. Inspect current issue/PR/CI state, reproduce defects, implement the smallest correct fix, verify exact-head behavior, perform adversarial falsification, run an architecture audit when blast radius warrants it, merge when justified, and reconcile post-merge state. For unspecified issue selection and claim-to-PR work, use the issue worker first. Do not use for review-only or reconcile-only requests where implementation should not be attempted.
---

# Issue Fixer

Own the issue lifecycle, not merely the code edit.

Default objective:

```text
understand -> establish failing condition -> fix -> verify -> falsify -> architecture audit when required -> merge -> reconcile -> close
```

Treat an issue as a bounded review unit, but treat the underlying architectural invariant as the unit of correctness.

This skill complements, rather than replaces, the queue-oriented issue worker. Use the issue worker to discover/select/claim unspecified work and hand off a PR; use issue-fixer when a concrete issue is already identified and the requested endpoint is actual verified closure.

## 1. Load current authorities first

For every substantive SearchKernel issue-fixing task, fetch fresh copies from `main` before making repository decisions:

- `superkelvint/searchkernel-cto-state/WORKFLOW.md`
- `superkelvint/searchkernel/AGENTS.md`

Also inspect when relevant:

- `superkelvint/searchkernel-cto-state/ISSUE_LABELS.md` for queue/claim semantics
- `superkelvint/searchkernel-cto-state/STATUS.md` for the active CTO frontier
- `superkelvint/searchkernel/docs/roadmap.md` when the active frontier or sequencing may change

Do not rely on a remembered or previously fetched version when current repository state is available. Current repository rules override this skill if they conflict.

Determine whether the current actor is operating as CTO/reviewer or implementation agent and obey the corresponding write boundaries in `WORKFLOW.md` and `AGENTS.md`.

## 2. Establish the real issue state

Before editing code:

1. Read the issue, labels, acceptance criteria, comments, and linked references.
2. Inspect open and recently merged PRs that may already implement or overlap the issue.
3. Inspect current `main` and the issue's likely code path.
4. Check relevant CI failures, including the failing job logs when they are material.
5. Determine whether the issue is:
   - still reproducible/current;
   - already fixed but unreconciled;
   - partially implemented;
   - blocked by a genuine product defect;
   - blocked only by environment/CI infrastructure;
   - overlapping another in-flight change;
   - part of a larger architectural closure cluster.

Prefer advancing an existing correct PR/branch over opening duplicate work. Do not treat a stale issue description, coding-agent claim, PR description, or old test result as project truth.

If the issue is already resolved on current `main`, skip implementation and perform the verification/reconciliation needed to justify closure.

## 3. Reproduce before fixing defects

For reported bugs, regressions, incorrect behavior, or correctness defects, follow the repository's regression-test-first rule:

```text
write/identify regression test
-> demonstrate failure on the defective implementation
-> change production code
-> demonstrate the regression passes
```

The reproduction must exercise observable behavior or the real implementation path. A source-text assertion or a test that already passed before the fix is not a valid defect reproduction.

If reproduction is impossible because the issue is environment-only, stale, or already fixed, record the concrete evidence rather than inventing a failing test.

## 4. Implement the smallest architecturally correct repair

Use the existing task branch/PR when appropriate; otherwise follow current repository worktree/branch/PR rules.

Keep the change bounded to the issue and its necessary correctness closure. Do not:

- weaken acceptance coverage;
- special-case fixtures or verifier inputs;
- introduce a second semantic path to avoid fixing the canonical one;
- silently change frozen contracts;
- hand-edit generated outputs when generation is authoritative;
- patch `upstream/vespa`;
- hide a real product failure as an environment failure;
- broaden into unrelated cleanup.

Resolve repository-internal dependencies that can safely be fixed as part of making forward progress. Stop only for a genuinely non-self-resolvable blocker.

Leave a durable breadcrumb when the repair uncovers a non-obvious invariant or failure mode a future maintainer would otherwise need to rediscover.

## 5. Verify the repair

Run the narrowest useful verification during implementation, then expand according to blast radius and current repository rules.

At minimum:

1. prove the regression/focused test now passes;
2. run the applicable package/component checks;
3. run required acceptance/verifier commands;
4. verify generated artifacts when their source changed;
5. use real native/Vespa execution when the contract or touched path requires it;
6. verify persistence/reopen when persistent state changed;
7. verify both sides of shared semantic paths when portable/canonical semantics changed;
8. inspect the final diff for unintended scope.

Distinguish product failures from CI/environment failures using evidence. Do not waive a failing product test because unrelated CI is noisy.

## 6. Perform adversarial falsification before a green conclusion

An issue fix is not ready to merge merely because the new test is green.

Always ask: **How could this fix be falsely green?** Scale the depth to the blast radius, but do not skip the question.

Challenge the implementation and verification with relevant cases from `references/review-gates.md`, especially:

- alternate semantic ingress paths;
- malformed and boundary inputs;
- absence versus empty/default semantics;
- persistence/reopen behavior;
- lifecycle races and interleavings;
- error-domain consistency;
- generated-artifact drift;
- silent fallbacks or dropped data;
- architectural bypasses;
- tests that never execute the changed branch;
- stranded/unmerged commits or a PR head that changed after verification.

A quick code scan can produce `UNVERIFIED` or identify a blocker. A positive conclusion requires enough adversarial evidence for the blast radius.

If the adversarial pass finds a defect, fix it in the same issue/PR when it is part of the same invariant and remains a bounded repair. Otherwise create/follow a separate issue without falsely closing the original acceptance criteria.

## 7. Run an architecture audit when the blast radius requires it

A full architecture audit is mandatory when the fix can affect one or more of these areas:

- lifecycle, concurrency, shutdown, ownership, or race behavior;
- canonical semantics or multiple semantic ingress paths;
- schema/protocol/API fidelity or generated bindings;
- persistence format, reopen, compatibility, or migrations;
- native/FFI/Vespa boundaries, ABI, ownership, or error propagation;
- result-tree/result-projection fidelity, grouping, sorting, ranking, or response semantics;
- transport framing, daemon behavior, cancellation, timeout, or cross-client parity;
- verification selectors/DAGs, acceptance harnesses, or other mechanisms that can make CI falsely green;
- security/trust boundaries or another high-blast-radius architectural invariant.

For these changes, audit the **architectural closure cluster**, not just the issue diff:

1. identify the invariant the issue is supposed to restore;
2. trace all materially equivalent ingress/execution paths;
3. confirm the canonical path remains singular where required;
4. inspect alternate clients/adapters/generated surfaces that can bypass it;
5. verify failure behavior is consistent across layers;
6. inspect persistence/reopen and lifecycle consequences when applicable;
7. compare with the independent oracle/source of truth when semantics depend on one, including pinned Vespa source when required;
8. ensure docs/capability claims do not exceed executable behavior;
9. ensure verification ownership actually covers the changed architecture;
10. identify adjacent open work that means the cluster is not yet architecturally closed.

For trivial mechanical/documentation-only changes, perform a lightweight architecture sanity check instead of a heavyweight audit.

## 8. Verify the exact PR head before merge

Before merge or approval:

1. read the current PR head SHA;
2. ensure the reviewed diff corresponds to that exact head;
3. ensure required checks/verification correspond to that head, not an earlier commit;
4. inspect unresolved review comments and merge conflicts;
5. confirm no head change occurred after the final verification;
6. confirm the issue acceptance criteria are actually satisfied.

If the head changed, re-run the verification needed for the changed surface before treating prior evidence as current.

Merge only when current repository rules permit it and the evidence supports it. Do not self-approve/self-merge when the current actor's role or repository policy forbids that action.

## 9. Post-merge reconciliation is part of the fix

Implementation or merge is not closure.

After a substantive merge:

1. fetch current `main` and confirm the intended merge is reachable;
2. confirm the issue/PR state reflects the actual result;
3. verify applicable CI on the merged state when required;
4. confirm acceptance criteria and architectural invariants still hold on `main`;
5. check for stranded commits, superseded PRs, stale labels, or duplicate work;
6. reconcile the architectural closure cluster: identify any remaining issue that prevents the invariant itself from being closed;
7. when operating as CTO/reviewer, update/reconcile `STATUS.md` and `docs/roadmap.md` if the active frontier materially changed, following current workflow rules;
8. call the issue `VERIFIED`/`CLOSED` only when the current workflow's definition of done is actually met.

If the merge only partially resolves the issue, leave it open and state the remaining acceptance gap concretely.

## 10. Handling CI failures while fixing an issue

Classify failures instead of blindly retrying:

- **Change-caused product failure:** diagnose and repair before merge.
- **Pre-existing product failure relevant to acceptance:** do not waive it; determine whether it blocks closure.
- **Known infrastructure/environment failure already fixed on `main`:** bring the PR up to current `main` and rerun the affected checks.
- **Transient runner failure with evidence of transience:** rerun the narrow failed job/run where possible.
- **Unrelated noisy failure:** document why it is unrelated, but still obtain the acceptance evidence required by the issue's blast radius.

Never change product semantics merely to appease a broken runner.

## 11. Default completion behavior

Unless the user explicitly asks for analysis/review only, keep making forward progress through the lifecycle. Do not stop at "I found the bug" or "PR opened" when the next step is safely executable.

The desired endpoint is verified closure, subject to repository permissions, required independent review, and genuinely external blockers.

When handing back status, be concise and evidence-based. Include:

- issue number and disposition;
- root cause;
- fix/PR/commit state;
- focused verification performed;
- adversarial falsification result;
- architecture-audit result or why only a lightweight check was appropriate;
- exact-head/merge state;
- post-merge reconciliation state;
- any concrete remaining blocker.

Use workflow confidence terms consistently (`UNVERIFIED`, `BLOCKED`, `NO BLOCKER FOUND`, `VERIFIED`, `CLOSED`) when the current SearchKernel workflow defines them.