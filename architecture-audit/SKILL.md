---
name: architecture-audit
description: Perform systematic evidence-based architecture and correctness audits of SearchKernel or a named subsystem. Use when the user asks to audit architecture, find architectural smells, systematically review a subsystem, inspect semantic boundaries, look for correctness bugs beyond a single PR, or run an adversarial repository audit. Ground SearchKernel audits in the live implementation-plan/audit checklist, current CTO workflow and AGENTS.md, trace full execution paths, challenge false-green tests and verifier gaps, compare against upstream/oracle behavior where required, and create deduplicated actionable GitHub issues for concrete findings with detailed verification-resolution plans.
---

# Architecture Audit

Audit the architecture that actually exists at an exact repository revision. Treat code, tests, verifier claims, docs, and prior agent reports as evidence to independently check, not as project truth.

This skill is for subsystem/repository audits. For a single implementation PR whose main goal is review/repair/merge, use the repository's PR workflow such as `pr-auto` instead.

## Audit modes

Choose the mode from the user's wording without asking when the intent is clear.

- **TRIAGE**: fast targeted inspection to locate likely blockers or choose where to investigate next. Never conclude that a capability is sound. Use `UNVERIFIED`, `NO BLOCKER IDENTIFIED YET - NOT VERIFIED`, or `NEEDS DEEP AUDIT`.
- **ADVERSARIAL AUDIT**: default for "systematic audit", "architecture audit", "look for architectural smells/correctness bugs", or equivalent requests. This is the minimum depth allowed to conclude `NO BLOCKER FOUND`.

Do not weaken the audit because the repository is large. Narrow the scope to the requested subsystem, then trace every relevant boundary that subsystem crosses.

## SearchKernel live authority

Before substantive SearchKernel audit work, fetch current live authority from `main`:

1. `superkelvint/searchkernel-cto-state/WORKFLOW.md`
2. `superkelvint/searchkernel/AGENTS.md`
3. `superkelvint/searchkernel/implementation-plan/audit/README.md`
4. `superkelvint/searchkernel/implementation-plan/audit/00-audit-method.md`
5. the selected subsystem audit file(s)
6. `18-cross-cutting-gates.md` when any cross-layer/product claim is involved
7. `19-audit-record-and-freeze.md` for evidence/disposition recording
8. `ISSUE_LABELS.md` from the CTO-state repo before creating findings as issues

Read `references/searchkernel.md` for reporting and issue-creation conventions. Use `scripts/audit_scope.py` only as a convenience for selecting likely audit modules; the live audit README remains authoritative.

## Workflow

### 1. Freeze the audit target

Record:

- repository and exact revision/head;
- requested subsystem or repository-wide scope;
- audit mode;
- relevant public/product claims;
- current implementation modules actually present in the tree.

Do not infer present modules from old roadmap prose or a historical checklist snapshot. Inventory the live tree first.

### 2. Select proof obligations

Start with the evidence model and repository-wide invariants in `00-audit-method.md`. Then load the specific module audit file(s) from the live modular index.

For a subsystem audit, also inspect adjacent layers needed to prove the complete path. Examples:

- client -> transport -> dispatcher -> IR;
- Portable API -> IR -> adapter -> Vespa engine/native boundary;
- lifecycle API -> persistence/open/reopen/native ownership;
- result generation -> canonical tree -> client projection;
- build/generation source -> checked/generated artifacts -> package/runtime.

Do not mark another module's obligation passed merely because the local layer looks correct.

### 3. Trace architecture, not filenames

For each material capability or invariant:

1. identify ingress paths;
2. trace semantic normalization/validation;
3. trace adapter/lowering boundaries;
4. trace native/runtime execution where applicable;
5. trace result/error propagation back to the caller;
6. inspect alternate ingress paths that should converge on the same semantics;
7. inspect persistence/reopen/lifecycle behavior where state crosses calls or processes;
8. inspect generated/configuration artifacts that can drift from source.

Look specifically for duplicated semantics, bypasses, leaky boundaries, silent fallbacks, approximation, unsupported requests being accepted, and backend-specific behavior leaking upward.

### 4. Gather evidence at the correct layer

Use the evidence classes and proof minima from the live audit method. Typical requirements include:

- architecture boundary: source + mechanical/static proof;
- parser/semantic behavior: source + unit/conformance, plus negative evidence for malformed/unsupported paths;
- generated-state claims: source + regeneration/freshness proof;
- Vespa behavior: source + verifier and upstream/oracle comparison where defined;
- public capability: lower-layer proof plus real public-path E2E;
- persistence/concurrency/recovery: behavioral proof plus hardening evidence;
- cross-language parity: the same frozen semantic scenario through every claimed first-party path.

Never use a lower-layer verifier to claim a higher-layer behavior.

### 5. Actively try to falsify green evidence

Ask how the implementation could still be wrong while all cited checks pass. Challenge relevant cases including:

- test never reaches the changed/claimed path;
- mock/scripted backend standing in for required native/runtime behavior;
- stale-head or stale generated-artifact evidence;
- absent vs present-empty or explicit zero/false semantics;
- malformed, overflow, Unicode, truncation, large-input, or unsupported combinations;
- close/reopen and historical persistence compatibility;
- lifecycle races and interleavings;
- alternate semantic ingress bypassing the canonical resolver;
- errors converted to success/default/fallback;
- docs/capability ledgers claiming more than executable evidence proves;
- verifier scripts regenerating expected data before comparison;
- CI or coverage exercising only one language/runtime layer.

A green command is evidence only if it could have gone red for the defect being excluded.

### 6. Check upstream/oracle behavior when semantics depend on it

When SearchKernel wraps or reproduces subtle Vespa behavior, inspect the pinned upstream/oracle source or executable oracle required by the contract. SearchKernel's implementation and tests alone are not sufficient for a negative conclusion about external semantics.

State what the oracle proves and its limits.

### 7. Turn concrete findings into durable issues

For each concrete architecture/correctness/verifier defect:

1. search existing open and recently closed issues for the same root cause;
2. reuse/update an existing issue when it already captures the finding;
3. otherwise create one bounded GitHub issue in `superkelvint/searchkernel`;
4. assign exactly one current workflow-state label, normally `status:ready` when actionable and unclaimed;
5. assign a priority using current `ISSUE_LABELS.md` definitions;
6. assign stable architecture area label(s) where they exist;
7. use the most accurate type (`type:bug`, `type:hardening`, `type:verification`, or `type:audit`), not `type:audit` mechanically for every finding.

The issue body must include enough evidence and verification resolution that an implementation agent can fix it without rediscovering the audit.

Do not create vague issues such as "clean up architecture" or "improve tests".

Do not implement findings during the audit unless the user explicitly asks to fix them. Keep `$issue` as the normal issue-to-PR workflow.

### 8. Record the audit disposition

When operating as the CTO/reviewer and current workflow authorizes it, update the required CTO audit ledger with the audited revision, scope, evidence, findings/issues, and disposition. Respect the CTO-state write boundary when operating as a coding agent rather than the CTO.

Use confidence terms exactly as defined by the current workflow:

- `UNVERIFIED`
- `BLOCKED`
- `NO BLOCKER FOUND`
- `VERIFIED`
- `CLOSED`

A completed adversarial audit may justify `NO BLOCKER FOUND`. It does not automatically justify `VERIFIED` unless the required acceptance evidence was independently checked.

### 9. Stop only at the actual audit boundary

A useful audit is complete when:

- the requested live scope has been inventoried;
- relevant checklist obligations and adjacent boundaries were examined;
- claims were tested with evidence at the correct layer;
- likely false-green modes were challenged;
- upstream/oracle behavior was checked where required;
- concrete findings were deduplicated and filed with verification resolution;
- unresolved proof gaps are explicitly `UNVERIFIED` rather than silently green;
- the required audit record was reconciled when authorized.

Do not stop after finding the first bug unless the user explicitly requested only one finding.

## Output

Keep the user-facing report concise and decision-useful. Default to:

```text
ARCHITECTURE AUDIT - <scope> @ <revision>

Disposition: <BLOCKED | NO BLOCKER FOUND | UNVERIFIED>

Findings:
- #<issue> <priority> <short concrete defect> - <one-line evidence>

Unverified / residual risk:
- <only material proof gaps>

Coverage:
- <audit modules / major execution paths examined>
```

Omit empty sections. If no blocker was found, state what adversarial evidence supports that conclusion; never substitute "I did not notice anything" for an audit disposition.

## GitHub access

Prefer the runtime-native authenticated GitHub connector and batch independent reads where possible. If it is unavailable or insufficient, use authenticated `gh` when the runtime permits it. Do not substitute public web search for private repository access.
