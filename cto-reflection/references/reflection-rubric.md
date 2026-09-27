# CTO Reflection Rubric

Use this rubric to cluster evidence from the reflection window. Do not force every category to appear.

## 1. Repeated human prompting

Look for cases where the user had to say variants of:

- continue / keep going;
- check again / re-check status;
- merge it / try merge again;
- bring it up to main;
- fix the other PRs too;
- update docs/tests after merge;
- do the adversarial review;
- reconcile the issue queue.

Ask whether the preceding workflow should already have included that next step.

## 2. Premature stopping

Flag when the agent stopped at an intermediate state even though the natural task implied more work, such as:

- identifying a fix without applying it;
- applying a fix without focused verification;
- opening/updating a PR without following CI to disposition;
- merging without post-merge reconciliation;
- fixing `main` without catching up affected open PRs when the dependency was obvious;
- finding stale issues without repairing queue state.

Do not flag a stop caused by a genuine external blocker or required user authorization.

## 3. Repeated discovery cost

Find facts repeatedly rediscovered across threads:

- which command runs the right test scope;
- which labels identify eligible work;
- which Docker/toolchain/native environment is canonical;
- which branch/PR is the active implementation;
- which build artifacts are immutable/cached;
- which client language owns a CI lane;
- which workflow/skill owns a task.

Repeated discovery usually belongs in a skill, authoritative repo doc, or command interface.

## 4. Tooling and environment churn

Look for unnecessary:

- full rebuilds;
- concurrent builds against shared targets;
- FlatBuffers/Vespa rebuilds when immutable artifacts should be reused;
- host/container mismatches;
- toolchain mutation or self-repair inside jobs;
- unrelated language CI fanout;
- repeated dependency provisioning;
- runner state repair that should be declarative/idempotent.

Separate root tooling defects from agent behavior. Do not "fix" a tooling defect by teaching a skill to retry wastefully.

## 5. Queue and lifecycle friction

Check whether issue/PR work required reconstructing state from prose, branches, or comments instead of canonical labels/state. Look for:

- unclear claimability;
- stale `status:*` labels;
- work blocked by stale branches;
- merged PRs with open/stale issues;
- green PRs waiting unnecessarily for review;
- dependency ordering discoverable only manually;
- affected PRs not rebased after a shared main fix.

Prefer canonical machine-filterable state.

## 6. Verification/false-green risk

Look for speedups or shortcuts that could accidentally weaken confidence:

- path filters that miss semantic dependencies;
- green CI without required native verification;
- tests using mocks where real Vespa is required;
- cached/generated artifacts that can drift;
- post-merge state not checked against exact `main` head;
- review based on PR description rather than exact diff;
- retries that turn intermittent infrastructure failure into an apparent pass without diagnosis.

A process improvement that increases false-green probability is not an improvement.

## 7. Skill quality problems

Classify skill failures precisely:

- **trigger failure:** matching requests do not invoke the right skill;
- **scope failure:** skill tries to own too much or overlaps another skill;
- **workflow gap:** a required step is missing;
- **closure gap:** skill stops before verification/reconciliation;
- **clarification tax:** skill asks questions answerable from current context/repo state;
- **state blindness:** skill fails to refresh authoritative files/current GitHub state;
- **evidence weakness:** skill accepts agent claims instead of independent verification;
- **output mismatch:** report is verbose but not actionable.

Prefer a targeted edit over a rewrite.

## 8. User/CTO habits

Give direct user feedback when the evidence supports it. Typical candidates:

- combining multiple independent goals into one ambiguous request;
- asking for a fix on `main` when a bounded issue/PR would preserve reviewability;
- repeatedly overriding a safe workflow in ways that create later cleanup;
- using inconsistent names for commands/processes that causes avoidable ambiguity;
- manually checking state that should be delegated to an automation;
- requesting broad "fix everything" work where a closure cluster or explicit priority would be clearer.

Also recognize productive habits worth keeping when they materially improve the process, such as insisting on adversarial review or calling out repeated build waste.

## 9. Prioritization

Prioritize by a qualitative combination of:

- recurrence frequency;
- human interruption cost;
- compute/runtime cost;
- correctness or false-green risk;
- breadth of tasks affected;
- ease and durability of the fix.

Prefer one durable fix that removes ten future prompts over ten local prompt tweaks.
