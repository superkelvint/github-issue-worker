---
name: issue-reconcile
description: Audit and repair GitHub issue-queue integrity across workflow labels, claim branches, linked/open/merged PRs, blockers, duplicates, stale ownership, and work already satisfied on the default branch. Use when asked to clean up the issue queue, remove stale issues, reconcile issue labels/state, find stranded claims, close issues that are already resolved, backfill or migrate queue taxonomy, or determine which issues are truly actionable. This is a fleet reconciliation workflow, not normal issue selection; batch repository state, prove semantic closures against current default, and make only evidence-backed state repairs.
---

# Issue Reconcile

Repair exception state in an issue queue. Normal workers should keep discovering work from canonical labels; this skill handles the rare cases where those labels or ownership records are wrong.

## Skill boundary

Use `issue` for one normal ready issue, `issue-followup` for one follow-up issue, and `pr-auto` to advance open PRs plus linked issue state. Use this skill when the queue itself may be stale, inconsistent, duplicated, stranded, or already resolved.

## Modes

- **Status**: requests such as "audit/show issue queue" are read-only.
- **Repair**: "clean up/reconcile/close stale issues" is action-oriented. Apply safe repairs and rerun consistency checks to a fixed point.

## Optimize tool use

Use Code Mode (`functions.exec`) for a small number of batched GitHub reads. Build cheap normalized records first; investigate bodies, branches, diffs, comments, or CI only for anomalies.

Collect where available: issue state/title/labels; priority/area/type; canonical claim branch; linked/open implementation PRs; merged PRs purporting to resolve it; explicit blockers/dependencies; duplicate/superseded references; and evidence that acceptance is satisfied on current default.

## Workflow

1. **Refresh authority.** Read live workflow/taxonomy rules. For SearchKernel fetch current `WORKFLOW.md`, `ISSUE_LABELS.md`, and `AGENTS.md`. Run a repository queue verifier when one exists.
2. **Snapshot the fleet.** Include all open implementation issues. Include closed issues only when checking stale labels, reopen drift, duplicate closure, or claimed resolution. Batch claim-branch and PR linkage discovery.
3. **Run structural policy.** Normalize issue records and run `scripts/reconcile_policy.py`. Structural mismatches identify investigations; they do not authorize guessed semantic state.
4. **Investigate anomalies only.** Distinguish active claims from stale branches, merged PRs from proven acceptance, and stale blockers from still-live dependencies.
5. **Prove closure before closing.** Identify resolving commit/PR/current behavior, verify issue acceptance criteria and architecture invariant against current default, and confirm the resolution is reachable from default. An agent claim or `Fixes #N` text is not enough.
6. **Repair safe state.** Remove workflow-state labels from closed issues; fix labels only when correct state is evidenced; release/delete stranded claims only after ruling out active ownership; move blocked work to ready only after its blocker is satisfied and no claim exists; close resolved/duplicate/superseded work only with concrete evidence.
7. **Do not guess.** Missing/multiple states, ready+claim, or in-progress-without-claim are ambiguous until ownership evidence resolves them. Leave them open as `NEEDS_CLASSIFICATION` when evidence is insufficient.
8. **Rerun to fixed point.** Rebuild affected state after mutations and rerun repository consistency verification until no additional safe repair follows.

## Canonical anomalies

```text
MISSING_STATE
MULTIPLE_STATES
CLOSED_WITH_STATE
READY_WITH_CLAIM
IN_PROGRESS_WITHOUT_CLAIM
STRANDED_CLAIM
BLOCKER_SATISFIED
RESOLVED_ON_DEFAULT
DUPLICATE_OR_SUPERSEDED
MISSING_PRIORITY
LEGACY_STATE_DRIFT
NEEDS_CLASSIFICATION
```

Branch/label mismatch is a queue defect, not a reason to weaken normal label-only issue discovery.

## SearchKernel

Read `references/searchkernel.md`. SearchKernel normal work is discovered from `status:ready`; `codex/issue-<number>` branches serialize claims. Reconciliation may inspect both. Preserve exactly one canonical workflow state, required priority, stable area labels, and a primary type where practical.

## Report

```text
ISSUE RECONCILIATION — <repo>
Queue: <open count>
Anomalies: <count>
Repairs applied: <count>
Remaining ambiguous: <count>

Repaired
- #123 CLOSED_WITH_STATE -> removed status:ready

Closed with evidence
- #125 RESOLVED_ON_DEFAULT — <commit/PR + acceptance evidence>

Needs classification
- #126 READY_WITH_CLAIM — <why ownership is ambiguous>

Queue verifier
- <command/result or connector equivalent>
```

Keep detailed evidence on the issue/PR; keep fleet output compact.

## Deterministic policy

`scripts/reconcile_policy.py` classifies normalized snapshots and intentionally refuses to guess ambiguous semantic state.

After policy changes run:

```bash
python3 -m unittest discover -s issue-reconcile/scripts -p "test_*.py" -v
```
