# PR Auto Architecture Audit Gate

Use this reference when `architecture_audit_requirement` is `FULL` or `DELTA`. Repository rules and live project contracts remain authoritative.

## Trigger checklist

Treat architecture audit as mandatory when the change can affect a cross-layer invariant involving:

- lifecycle, concurrency, shutdown, ownership, or races;
- canonical semantics or multiple semantic ingress paths;
- schema/protocol/API fidelity or generated bindings;
- persistence, reopen, compatibility, or migrations;
- native/FFI/Vespa boundaries, ABI, ownership, or error propagation;
- result-tree/projection fidelity, grouping, sorting, ranking, or response semantics;
- transport/daemon/cancellation/timeout/client parity;
- CI selectors, verification DAGs, acceptance harnesses, or verifier ownership;
- security/trust boundaries or another high-blast-radius architectural invariant.

A transport or verification-architecture PR can require this audit even when ordinary/adversarial code review is otherwise modest.

## Full architecture audit

Audit the invariant, not just the changed lines.

1. State the invariant the PR must preserve or restore.
2. Enumerate the architectural closure cluster: all material ingress, execution, persistence, transport, client, generated, and verification paths that can affect that invariant.
3. Confirm canonical ownership remains singular where required; look for duplicate semantics or bypasses.
4. Check equivalent positive and negative behavior across alternate paths.
5. Check error-domain and failure-behavior consistency across layers.
6. Check lifecycle and persistence/reopen consequences when relevant.
7. Check ABI/ownership/generated-artifact compatibility when relevant.
8. Compare against the independent oracle/source of truth when one exists.
9. Check documentation/capability claims against executable behavior.
10. Check that CI/verifier selection actually owns every affected path.
11. Identify adjacent open work that prevents the closure cluster from being called closed.

A full audit result should say which invariant and closure cluster were inspected, what bypasses were challenged, any gap found/fixed, and any residual architectural risk.

## Delta architecture audit

Use a delta audit only when an earlier full architecture audit exists and the new head changes narrow tests/docs/mechanical cleanup without reopening the audited architecture.

For the delta:

- inspect the exact diff since the last audited SHA;
- confirm it does not add/change an architecture trigger or broaden the closure cluster;
- confirm the prior audit conclusions still hold;
- rerun any verification directly affected by the delta;
- record the new exact head.

If the delta changes semantics, boundaries, ownership, client/transport parity, persistence/lifecycle behavior, verifier selection, or another architecture trigger, perform a full audit instead.

## Durable record

Record the audit on the PR using:

```text
<!-- pr-auto:architecture-audit -->
PR-AUTO ARCHITECTURE AUDIT
head_sha: <40-char SHA>
disposition: NO_BLOCKER_FOUND | CHANGES_REQUIRED | VERIFIED
scope: <invariant and closure cluster>
reviewed_at: <ISO timestamp if available>
```

Only an exact-head `NO_BLOCKER_FOUND` or `VERIFIED` record satisfies the merge gate. A stale record may guide full-versus-delta re-audit but never unlock merge directly.
