# Issue Fixer Review Gates

Use this reference during adversarial falsification and architecture auditing. Apply only the gates relevant to the changed surface, but explicitly consider whether each category can make the fix falsely green.

## False-green checklist

### Coverage and test validity
- Does the regression fail before the production fix?
- Does the test execute the changed production branch rather than a mock/text proxy?
- Can fixture shape or hard-coded IDs make the test pass without general correctness?
- Does a broad test report green while silently skipping the relevant capability?
- Are required native/real-engine paths actually running?

### Semantic ingress
- Do Rust builders, FlatBuffers/protocol decode, textual query forms, convenience helpers, and language clients converge on the intended canonical semantics?
- Is there an alternate path that bypasses validation, normalization, or conversion?
- Are equivalent forms actually equivalent for positive and negative cases?

### Boundary and malformed inputs
- Empty versus absent versus default values.
- Zero, one, max, overflow/underflow boundaries.
- Truncated/malformed protocol data.
- Unicode, long strings, repeated/multi-valued inputs.
- Unsupported combinations fail explicitly rather than degrading silently.

### Error behavior
- Same failure maps to the same error domain across paths.
- No panic/unwind/exception crosses a native boundary.
- No fallback turns an unsupported/error case into plausible but wrong output.
- Cleanup after failure leaves lifecycle/handles/state valid.

### Lifecycle and concurrency
- Open/close/reopen sequences.
- Concurrent read/write/close and cancellation where relevant.
- Failure during initialization or mutation.
- Double-close/stale-handle/use-after-close style behavior.
- Interleavings that can expose partial state.

### Persistence and compatibility
- Close/reopen preserves behavior.
- Existing supported manifests/formats still open.
- Failed writes do not corrupt or partially commit state.
- Migration/version handling is explicit and test-covered.

### Result fidelity
- No reordering, dropping, synthetic values, or lossy projection.
- Tree/source-of-truth invariants remain intact.
- Empty collections, null/absence, sort values, features, coverage, timing, metadata, and errors preserve semantics.
- Nested groups/aggregations/hits survive round trips when relevant.

### Native/FFI/ABI
- ABI version and generated bindings agree with the header/manifest/contracts.
- Ownership, allocation, borrowing, and free rules remain clear.
- C++ exceptions are contained; Rust panics do not cross FFI.
- Integer widths/signs and optional values match across the boundary.
- SDK/generated artifacts are not stale.

### Schema/protocol/generated artifacts
- Source schema and generated bindings are synchronized.
- Field order/union tags/numeric policies remain compatible.
- Old supported encodings or persisted versions still behave as promised.
- Client generators and conformance fixtures represent the same contract.

### CI and verification architecture
- The selector/gate actually schedules verification for this changed surface.
- A path rename/new subsystem does not bypass verification ownership.
- The CI result belongs to the exact reviewed PR head.
- Environment fixes on `main` have actually been incorporated into the PR.

### Repository/integration state
- No relevant fix remains only in a local or unmerged commit.
- No duplicate PR is the real owner of the repair.
- Merge/rebase conflict resolution did not drop part of the fix.
- Post-merge `main` contains the reviewed implementation.

## Architecture audit trigger guidance

Run a full architecture audit when a defect can violate a cross-layer invariant or when a local fix may leave another execution path incorrect. Typical triggers:

- lifecycle/concurrency;
- persistence/reopen;
- canonical query/filter/ranking semantics;
- protocol/schema/generated code;
- native/FFI/ABI;
- result projection or grouping;
- daemon/transport/client parity;
- CI/verifier selection and acceptance architecture.

A full audit should identify the invariant, enumerate the closure cluster, inspect all material ingress/execution paths, and state whether the cluster is actually closed. Do not convert "this PR is fixed" into "the architecture is closed" without that evidence.