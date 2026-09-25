# SearchKernel Architecture Audit Reference

Use this file for SearchKernel-specific audit orchestration. Project truth remains in the live repositories; do not copy historical checklist contents into the skill and treat them as current.

## Live project sources

Fetch these from `main` for each substantive audit:

- `superkelvint/searchkernel-cto-state/WORKFLOW.md`
- `superkelvint/searchkernel-cto-state/ISSUE_LABELS.md`
- `superkelvint/searchkernel/AGENTS.md`
- `superkelvint/searchkernel/implementation-plan/audit/README.md`
- `superkelvint/searchkernel/implementation-plan/audit/00-audit-method.md`
- selected numbered module audit files
- `superkelvint/searchkernel/implementation-plan/audit/18-cross-cutting-gates.md`
- `superkelvint/searchkernel/implementation-plan/audit/19-audit-record-and-freeze.md`

When native/Vespa behavior is in scope, also read the current `reference/vespa/README.md` and the contract/oracle files for the claimed behavior before treating a verifier as authoritative.

## Finding threshold

Create an issue when there is a concrete, actionable defect or missing proof obligation that matters to supported behavior. Good findings include:

- duplicated or bypassed portable semantics;
- contract accepted at one layer but dropped/rejected/approximated later without the promised error;
- result/error fidelity loss;
- persistence/reopen incompatibility;
- lifetime/race/failure-atomicity problems;
- generated-state drift that can ship or pass falsely;
- public capability claim without the required executable evidence;
- verifier/test that cannot falsify the behavior it claims to prove;
- undocumented architectural ingress that bypasses verification ownership.

Do not file an issue for an item that is merely uninspected during a partial audit. Mark it `UNVERIFIED` in the audit report instead.

## Issue body template

Use a bounded title naming the failed invariant or behavior. The body should contain:

```markdown
## Problem
<Concrete architecture/correctness/verifier defect.>

## Evidence
- Audited revision: `<sha>`
- Audit obligation(s): `<stable checklist IDs>`
- Source/runtime evidence: `<paths, symbols, commands, behavior>`
- Why current tests/verifiers can be falsely green, if applicable.

## Expected behavior
<The invariant or externally verified behavior that must hold.>

## Scope / constraints
<Relevant architecture boundaries, frozen contracts, and forbidden shortcuts.>

## Verification resolution
1. <Regression/negative/static proof that fails before repair when applicable.>
2. <Focused verification proving the repaired layer.>
3. <Cross-boundary/E2E/native/oracle proof required by blast radius.>
4. <Generated/docs/capability reconciliation if the finding affects them.>

## Closure
The issue is resolved only when the implementation and the verification resolution above are satisfied at the exact repaired head; green lower-layer checks alone are insufficient.
```

For a correctness bug, require regression-test-first behavior where the repository workflow requires it.

## Labeling

Read current `ISSUE_LABELS.md` before writing labels. Normally:

- actionable/unclaimed finding: `status:ready`;
- priority: exactly one of `priority:p0` through `priority:p3` according to current definitions;
- area: stable subsystem labels such as IR/protocol/searchkerneld/native/Vespa/client/persistence/CI where they exist;
- type: choose the actual work:
  - `type:bug` for incorrect supported behavior;
  - `type:hardening` for robustness/lifecycle/resource safety work;
  - `type:verification` for a concrete missing/false-green proof gate;
  - `type:audit` only when the issue itself is further bounded investigation rather than a known defect.

Do not invent a new area label during an audit merely for convenience; use existing labels or leave the area unlabeled and mention the routing gap.

## Priority guidance

Use repository definitions, not emotional language:

- P0 only for immediate correctness/data-loss/safety/build-release/architectural blockers.
- P1 for important correctness/hardening on the active frontier.
- P2 for normal planned engineering work.
- P3 for low-urgency cleanup/ergonomics/non-blocking improvement.

When uncertain between adjacent priorities, prefer the less severe label and explain the blast radius in the issue body rather than inflating priority.

## Deduplication

Before creating a finding issue, search by the concrete invariant, affected symbol/path, and characteristic failure mode. Check both open and recently closed issues when a regression may have reappeared.

Prefer one root-cause issue over multiple symptom issues. Split findings only when repairs are independently reviewable and can close independently.

## Audit ledger

The current CTO workflow requires adversarial audit evidence/disposition to be recorded in `AUDITS.md`. Only mutate CTO-owned control-plane files when acting with CTO authority. Coding agents must respect the current write boundary and report the needed ledger update rather than editing forbidden paths.
