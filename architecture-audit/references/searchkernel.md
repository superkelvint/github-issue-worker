# SearchKernel architecture-audit routing

Use live repository files as authority; this reference only tells the skill where to look.

## Required live reads

For substantive SearchKernel audits fetch from current `main`:

- `superkelvint/searchkernel-cto-state/WORKFLOW.md`
- `superkelvint/searchkernel/AGENTS.md`
- `superkelvint/searchkernel/docs/reading-the-codebase.md`
- relevant architecture/specification/capability/limitations files
- relevant `implementation-plan/audit/*.md`

When issue creation or queue state changes are involved, also fetch:

- `superkelvint/searchkernel-cto-state/ISSUE_LABELS.md`

Do not bundle copies of those documents here; they change.

## Audit checklist routing

Always read `implementation-plan/audit/00-audit-method.md`.

Common subsystem mappings:

- portable/API contract -> `01-api-portable-contract.md`
- FlatBuffers build/generation -> `02-flatbuffers-build.md`
- protocol -> `03-searchkernel-protocol.md`
- filter -> `04-searchkernel-filter.md`
- IR/portable semantics -> `05-searchkernel-ir.md`
- testkit -> `06-searchkernel-testkit.md`
- Rust product API -> `07-searchkernel-rust-api.md`
- canonical dispatch -> `08-searchkernel-dispatch.md`
- IR to backend lowering -> `09-searchkernel-ir-adapter.md`
- Rust/native ABI declarations -> `10-searchkernel-vespa-bindings.md`
- safe Vespa engine wrapper -> `11-searchkernel-vespa-engine.md`
- C++ native adapter -> `12-native-vespa-cpp.md`
- daemon / transport host -> `13-searchkerneld.md`
- Python client -> `14-client-python.md`
- TypeScript client -> `15-client-typescript.md`
- build/dev tooling -> `16-tools.md`
- acceptance/oracle/verifier infrastructure -> `17-reference-verifiers.md`

For any path crossing more than one subsystem also read `18-cross-cutting-gates.md`.
When recording/finalizing an audit, consult `19-audit-record-and-freeze.md`.

## Architectural invariants to keep visible

SearchKernel is a thin wrapper around Vespa. The important high-level invariants include:

- FlatBuffers is the canonical portable contract.
- `searchkernel-ir` owns portable semantics, validation, defaults, and normalization.
- Rust uses the direct in-process semantic path rather than serializing through gRPC.
- Non-Rust clients use generated FlatBuffers + generated gRPC plumbing with thin facades.
- Transport must not become another semantic implementation.
- `searchkernel-ir-adapter` is the integration boundary between portable meaning and Vespa-specific execution.
- The Rust/native boundary is isolated in bindings/C++ adapter layers; Vespa types must not leak into public product APIs.
- Result conveniences are projections over canonical result meaning, not alternate semantics.
- Pinned Vespa behavior is an external authority for Vespa-owned semantics.

Always confirm these against current repository docs before using them as evidence.

## Issue filing

SearchKernel remediation issues must be created with canonical queue labels in the same creation operation. Ordinary actionable findings use `status:ready`, exactly one priority, one or more stable `area:*` labels, and the work's actual `type:*`.

Do not use a broad audit umbrella issue as a substitute for bounded remediation issues. Reuse an existing issue only when its acceptance criteria truly cover the finding.
