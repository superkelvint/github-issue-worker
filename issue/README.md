# Issue Worker

The `$issue` skill runs one GitHub issue from selection through pull request.

Normal work discovery is label-driven:

```text
is:issue is:open label:status:ready
```

The worker orders ready issues by repository priority, then age. Search Kernel uses
`priority:p0` through `priority:p3`, plus namespaced `area:*` and `type:*`
labels for routing.

It supports:

- optional hard filtering such as `$issue hnsw` or `$issue "schema fidelity"`,
  applied within the `status:ready` queue;
- race-safe claiming through the canonical `codex/issue-N` remote branch;
- mandatory `status:ready -> status:in-progress` claim-state transition;
- mandatory dedicated Git worktree isolation for every claimed issue;
- regression-test-first bug fixes;
- focused implementation and verification;
- pull-request handoff without auto-merge;
- safe release back to `status:ready`, `status:blocked`, or
  `status:needs-followup`;
- mandatory terminal cleanup: after a successful claim, the worker must either
  open/preserve an implementation PR or release the claim.

See `SKILL.md` for the authoritative workflow.
