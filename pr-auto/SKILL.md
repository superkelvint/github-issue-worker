---
name: pr-auto
description: Autonomously manage a GitHub pull-request fleet as a fix-forward control loop with minimal conversational tool churn. Use when the user says "pr auto", asks for a PR status update, says "check again", "move every PR forward", "review and merge the green ones", "get the open PRs moving", or otherwise wants open PRs advanced rather than merely summarized. Batch GitHub reads through Code Mode, repair bounded CI/code/conflict problems when possible, review/merge when repository rules permit, track adversarial-review evidence by exact head SHA, reconcile after changes, and continue until no safe forward action remains.
---

# PR Auto

## Objective

Treat pull-request management as a control loop, not a report-generation task.

When invoked as `pr auto` with no limiting qualifier, inspect the whole relevant open-PR fleet, move every PR as far forward as safely possible, repair bounded blockers instead of merely describing them, re-snapshot changed state, and repeat until reaching a fixed point for the current invocation.

A fixable problem is work to perform, not a reason to stop.

## Invocation semantics

Interpret these forms as equivalent full-auto requests when repository context is clear:

- `pr auto`
- `PR auto`
- `move every PR forward`
- `move the open PRs forward`
- `review and merge everything ready`
- `check the PRs and get them moving`

Interpret `pr auto status` as read-only fleet inspection.

Interpret `pr auto <PR>` as the same control loop scoped to one PR.

In an ongoing PR-auto conversation, interpret a terse `check again`, `status`, `continue`, or `move them forward` as continuation of the same fleet-management goal unless the user clearly changes scope.

## Default authority

`pr auto` itself authorizes ordinary repository actions needed to advance PRs, including:

- updating stale PR branches through repository-approved mechanisms;
- rerunning a plausibly transient failed job once when evidence supports it;
- diagnosing and repairing CI/tooling problems;
- resolving bounded merge conflicts;
- implementing bounded code/test fixes on the existing PR when repository rules allow it;
- pushing fixes and updating the existing PR;
- reviewing PRs that are ready for review;
- recording adversarial-review evidence when an actual adversarial review has been completed;
- merging PRs that satisfy current repository review/verification policy;
- reconciling linked issue/PR state after merge.

Do not interpret `pr auto status` as write authorization.

Do not bypass repository rules, ownership rules, required review gates, or unavailable verification merely to advance state.

## Core optimization rule: orchestrate, do not chatter with tools

Use Code Mode (`functions.exec`) to batch independent GitHub connector calls.

- Fan out independent reads with `Promise.all(...)`.
- Return compact normalized records from the orchestration call rather than raw connector payloads.
- Do not make one assistant tool call per PR, status, workflow, job, comment, or file when they can be collected together.
- Perform dependent reads in a few stages: fleet discovery -> targeted evidence -> actions -> changed-state refresh.
- Re-fetch only PRs whose head/state changed unless a full resnapshot is needed to discover newly unblocked work.
- Fetch full job logs only for failed jobs whose cause is not already explicit.
- Fetch full diffs/source/specs only for PRs that actually need review or repair.
- If an exact GitHub action is not obvious, inspect `ALL_TOOLS` inside Code Mode and use the matching action. Do not guess tool names.

The goal is a handful of orchestration calls containing many GitHub API operations, not dozens of conversational tool round trips.

## SearchKernel live authority

For substantive SearchKernel PR management, review, repair, merge, audit, reconciliation, or CTO work, fetch current live authority before acting:

1. `WORKFLOW.md` from `main` of `superkelvint/searchkernel-cto-state`.
2. `AGENTS.md` from `main` of `superkelvint/searchkernel`.
3. `BUILDING.md` when build, environment, toolchain, native SDK, linker, compiler, or verification behavior matters.
4. Other contracts/specifications only when the affected PR requires them.

Batch these reads where possible. Follow current repository state rather than bundled memory.

For SearchKernel-specific heuristics and review tracking, read `references/searchkernel.md` when relevant.

## Stage 1 — Build one fleet snapshot

First discover the relevant open PR fleet. Prefer the repository's explicit review/handoff signals, but include anomalous open PRs whose state itself needs reconciliation.

For every PR, gather cheap evidence in parallel and normalize it into a compact record containing, where available:

- PR number/title/URL;
- exact `head_sha` and base branch/SHA;
- draft/ready state;
- labels;
- mergeability/conflict state;
- author/ownership clues;
- changed filenames and approximate blast radius;
- linked issue(s);
- CI/check summary for the exact head;
- exact-head workflow runs;
- behind/ahead divergence from current base branch;
- unresolved review/follow-up state;
- adversarial-review record for the exact head, if any.

Do not fetch every full diff or every CI log during this stage.

## Stage 2 — Classify every PR

Assign one primary next-action state:

- `MERGE_NOW` — repository policy is satisfied at the exact current head.
- `REVIEW_NOW` — ready for reviewer/CTO inspection; deeper review still required.
- `ADVERSARIAL_REVIEW_REQUIRED` — blast radius requires an adversarial pass and no current-head record exists.
- `UPDATE_FROM_MAIN` — stale relative to base and current main likely contains prerequisites/fixes.
- `FIX_CI` — red CI needs diagnosis or repair.
- `RESOLVE_CONFLICT` — bounded merge conflict blocks progress.
- `FIX_IMPLEMENTATION` — concrete bounded code/test/review defect can be repaired now.
- `FOLLOW_UP_REQUIRED` — repair is too broad, separately reviewable, or current repo workflow requires handoff.
- `ACTIVE_WORK` — another worker is legitimately still implementing; avoid interference.
- `WAITING` — genuine external/non-self-resolvable blocker.
- `STALE_OR_SUPERSEDED` — PR/issue state appears obsolete and requires evidence-based reconciliation.

Do not stop after classifying. The classification exists to drive action.

## Stage 3 — Advance the fleet

Process all independent safe actions in batches where possible.

A useful default ordering is:

1. merge PRs already fully eligible;
2. update stale PRs from current base;
3. repair red CI;
4. resolve bounded conflicts;
5. implement bounded code/test fixes;
6. review PRs ready for CTO/reviewer action;
7. perform adversarial reviews where required;
8. merge newly eligible PRs;
9. reconcile linked issues and stale PR state.

Ordering may change when one PR unblocks another. Prefer the sequence that maximizes safe forward progress.

### Update stale PRs

If current base contains relevant infrastructure, CI, dependency, or prerequisite fixes, update the PR instead of reimplementing them.

After branch movement, discard old green/red conclusions and bind all further evidence to the new exact head.

### Repair CI

Use the same principles as `ci-fixer`:

- isolate first meaningful failure;
- distinguish product regression from CI fanout, runner/toolchain/container, generated drift, build/link/native SDK, harness defects, stale-head problems, and plausible flakes;
- fetch only relevant failed-job logs;
- repair the root cause when bounded;
- do not rerun until green;
- verify the exact new head after a repair.

### Resolve conflicts

Resolve simple, mechanically bounded conflicts when repository rules and available tooling allow it. Re-run required verification against the resulting exact head.

Do not silently choose semantics when the conflict requires a product/architecture decision.

### Fix implementation defects instead of merely reporting them

When review, CI, or inspection reveals a bounded defect that can safely be fixed on the existing PR, implement the fix rather than stopping with a complaint.

Follow repository-specific rules. In repositories requiring regression-test-first for reported correctness defects:

1. add the smallest executable regression reproducing the defect;
2. observe the pre-fix failure;
3. implement the smallest correct production repair;
4. prove the regression passes;
5. run broader verification proportional to blast radius;
6. push/update the existing PR;
7. re-review the changed delta at the new exact head.

Escalate to `FOLLOW_UP_REQUIRED` only when the repair is materially broader/separately reviewable, another active worker owns it, verification cannot be obtained, or a genuine decision is required.

## Stage 4 — Review and adversarial-review tracking

Normal review and adversarial review are different.

The skill may organize evidence for an adversarial review, but must never claim an adversarial review occurred merely because CI is green, a diff was skimmed, or metadata was collected.

Only record an adversarial review after the model actually performs the repository-required adversarial reasoning for that PR and head.

### Exact-head review identity

Treat adversarial review as valid only for the exact reviewed `head_sha`.

A new commit automatically makes the prior review stale, even if the change appears small. A delta re-review may be sufficient when repository policy permits, but the new exact head still needs an explicit current record.

### Durable tracking record

Prefer a machine-readable PR comment rather than a plain label, because labels are not SHA-bound.

Use a marker similar to:

```text
<!-- pr-auto:adversarial-review -->
PR-AUTO ADVERSARIAL REVIEW
head_sha: <40-char SHA>
disposition: NO_BLOCKER_FOUND | CHANGES_REQUIRED | VERIFIED
scope: <short description>
reviewed_at: <ISO timestamp if available>
```

Include concise evidence/findings below the marker when useful.

When building the fleet snapshot, inspect PR comments for this marker and select the latest record matching the exact current head.

Expose normalized review state as:

- `CURRENT:NO_BLOCKER_FOUND`
- `CURRENT:CHANGES_REQUIRED`
- `CURRENT:VERIFIED`
- `STALE:<reviewed_sha>`
- `NONE`
- `N/A` for changes that current repository policy explicitly treats as too trivial/mechanical to need adversarial review.

Do not add a generic `adversarial-reviewed` label as the sole source of truth.

If the current repository workflow requires another durable audit ledger in addition to the PR record, update that ledger too.

## Stage 5 — Exact-head verification and merge

Before merging any PR:

- re-fetch current PR metadata;
- verify the expected head has not moved;
- verify applicable required checks against that exact head;
- ensure required review/adversarial-review evidence is current;
- reconcile issue acceptance criteria and relevant architecture/contracts;
- challenge likely false-green modes based on blast radius;
- use expected-head protection when the merge action supports it.

A green run attached to an older SHA is not evidence for the current PR.

After merge, verify the merge result is reachable from current base/main and reconcile linked issue/PR state as required by the repository.

For SearchKernel substantive work, apply the live CTO/repository definition of done rather than treating `merged=true` as closure.

## False-green challenge

Scale this to blast radius. Relevant checks include:

- workflow/check belongs to an old head;
- required lane was skipped or never selected;
- CI selector accidentally excluded the changed subsystem;
- rerun masked a deterministic failure;
- test never reached the modified path;
- generated artifacts drifted from sources;
- local/runner environment supplied undeclared dependencies;
- native behavior was not exercised where required;
- error was swallowed into a successful fallback;
- persistence/reopen path was not exercised;
- absence and present-empty semantics disagree;
- concurrency/interleavings remain untested;
- alternate semantic ingress bypasses the changed path;
- merge happened but issue acceptance criteria remain unresolved.

## Stage 6 — Re-snapshot and iterate to a fixed point

After any batch of actions that changes heads, merge state, issue state, labels, or CI:

1. refresh changed PRs immediately;
2. perform a broader fleet resnapshot when merges may have unblocked or obsoleted other PRs;
3. reclassify;
4. execute newly available safe actions;
5. continue until no additional safe forward action remains in the current invocation.

Do not stop merely because one action succeeded. For example, if updating a stale branch turns it green and merge-eligible, continue through review/merge rather than waiting for another user prompt.

Do not promise to continue later. Reach the current fixed point now.

## When to stop

Stop advancing a PR only for a concrete reason such as:

- another active worker owns conflicting implementation work;
- required credentials/permissions/tooling are unavailable after documented recovery attempts;
- required external service or native environment cannot be obtained;
- a product/specification/architecture decision is genuinely needed;
- the required fix is materially larger than the PR's bounded scope and current workflow requires separate work;
- required verification cannot be truthfully completed.

State the first non-self-resolvable blocker and the next concrete action. Do not use an ordinary fixable repository problem as a blocker.

## Output format

Keep the final fleet report compact. Lead with what changed, not a giant inventory.

Default structure:

```text
PR AUTO — <repo>

Merged: <count>
  #... <short result>

Advanced: <count>
  #... <new state/action>

Repaired: <count>
  #... <fix + exact new head>

Reviewed: <count>
  #... <normal/adversarial status>

Still blocked/waiting: <count>
  #... <first concrete blocker>

Fleet fixed point: <yes/no and why>
```

Omit empty sections. Mention exact SHA where it matters for verification/review identity. Avoid listing every successful check unless requested.

For `pr auto status`, report the same normalized states but perform no writes.
