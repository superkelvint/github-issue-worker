# SearchKernel coverage-risk guide

SearchKernel is a thin Rust/product layer over Vespa. Coverage work must respect that architecture: Rust line coverage can show whether SearchKernel Rust paths executed, but it does not prove Vespa C++ behavior or replace real-engine/native verification.

## Risk-first path map

Treat these areas as high-priority candidates when coverage evidence shows meaningful gaps. Do not assume they are gaps without measuring current HEAD.

- `core/crates/searchkernel-ir`: canonical portable semantics, defaults, validation, normalization, presence semantics.
- `core/crates/searchkernel-dispatch`: untrusted envelope verification, protocol/version routing, error construction, canonical dispatch.
- `core/crates/searchkernel-filter`: parser/binder limits, clause-local bindings, malformed/boundary input, typed resolution.
- `core/crates/searchkernel-ir-adapter`: semantic lowering; risk of loss, mismatch, alternate lowering, unsupported behavior, silent fallback.
- `core/crates/searchkernel-vespa-bindings`: Rust/native ownership, lifetimes, ABI/error conversion, failure cleanup.
- `core/crates/searchkernel-vespa-engine`: lifecycle, reopen/recovery, mutation/search state, result fidelity, native failures.
- `searchkerneld`: framing, lifecycle/shutdown, limits, transport-vs-portable error domains, UDS/TCP behavior.
- persistence/reopen compatibility tests and historical fixture handling.
- result projection/conversion: canonical tree preservation, nested groups/hits/features, non-finite/error cases.

SDK facade gaps matter when they can cause semantic drift, presence loss, numeric coercion, result corruption, or client-specific behavior. Cosmetic convenience coverage is lower risk than canonical semantics.

## Native caveat

The normal Rust cargo-llvm-cov report does not measure SearchKernel's Vespa C++ implementation when that native code is compiled by the existing GCC path. Never interpret high Rust coverage as high native coverage.

When the target behavior crosses the native boundary, retain or add the appropriate real-Vespa verifier/E2E evidence in addition to Rust coverage. If native C++ line coverage is desired, treat that as a separate toolchain project: cargo-llvm-cov FFI coverage requires compatible Clang/LLVM instrumentation and must not silently replace the pinned native build contract.

## SearchKernel false-green checklist

Challenge these specifically:

- Rust builder and FlatBuffers/gRPC ingress do not converge on equivalent semantics.
- textual and structured filters cover different cases or parameter scope leaks.
- absent vs explicit empty fields are collapsed.
- malformed FlatBuffers/protocol versions take an untested bypass.
- native open/close failure leaves a handle or wrong error kind.
- mutation success is covered but reopen persistence is not.
- grouping/result convenience views pass while canonical tree ordering/data is wrong.
- native adapter fallback or unsupported behavior is silently dropped.
- concurrency/lifecycle tests execute methods without forcing adverse interleavings.
- tests prove RecordingBackend behavior where acceptance requires real Vespa.

Coverage improvement is complete only when the selected risk is materially reduced by assertions plus the applicable independent verifier.
