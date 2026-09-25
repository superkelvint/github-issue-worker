# SearchKernel issue reconciliation

Use current repository state as authority. Fetch these live before reconciliation:

- `superkelvint/searchkernel-cto-state/WORKFLOW.md`
- `superkelvint/searchkernel-cto-state/ISSUE_LABELS.md`
- `superkelvint/searchkernel/AGENTS.md`

When available in a working checkout, run:

```bash
python3 tools/check-issue-queue.py --repo superkelvint/searchkernel
```

Treat its output as an anomaly detector, not proof of semantic closure.

## Canonical workflow states

Open implementation issues use exactly one of:

```text
status:ready
status:in-progress
status:blocked
status:needs-followup
```

Closed issues retain none of those workflow-state labels.

Normal unclaimed work discovery remains:

```text
is:issue is:open label:status:ready
```

Do not change normal workers to inspect PRs/branches just because reconciliation occasionally finds drift.

## Claim invariant

The canonical `codex/issue-<number>` branch is the race-safe claim lock. The searchable state representation is `status:in-progress`.

Important inconsistencies include:

- ready + canonical claim branch;
- in-progress without the canonical claim branch;
- closed issue retaining a status label;
- open implementation issue with no status label;
- multiple status labels;
- stale claim branch preventing a genuinely reopened/ready issue from being claimable.

Before deleting a claim branch or releasing in-progress state, verify there is no active implementation PR/worker that legitimately owns it.

## Semantic closure

A merged PR is evidence, not automatic proof that an issue is resolved. Before closing a stale issue:

1. identify the resolving commit/PR;
2. confirm it is reachable from current `main`;
3. map current behavior/tests/contracts to the issue acceptance criteria;
4. ensure no known regression/follow-up reopens the invariant;
5. then close/remove workflow-state labels as required.

Blocked issues should move back to ready only when their blocker is actually satisfied and the issue is otherwise actionable/unclaimed.
