# SearchKernel CI Failure Patterns

Use this reference only for SearchKernel investigations. These are hypotheses to test, not automatic conclusions. Current `WORKFLOW.md`, `AGENTS.md`, `BUILDING.md`, workflow files, and exact-head CI evidence remain authoritative.

## Contents

1. Stale PR head / fix already on main
2. Language-unrelated CI fanout
3. Runner/toolchain mutation
4. Shared build-directory contamination
5. Container image mismatch
6. FlatBuffers/generated drift
7. Native SDK/linker failures
8. Dev/doctor/universe harness failures
9. Exact-head and closure traps

## 1. Stale PR head / fix already on main

Symptoms:

- many old PRs fail with an error already repaired on main;
- PR head predates a CI/tooling repair;
- failure occurs in infrastructure untouched by the PR.

Test:

- compare current `main` to PR head;
- identify the relevant main commit/file change;
- update the PR through the repository-approved mechanism;
- verify new exact head rather than patching the same fix again.

## 2. Language-unrelated CI fanout

Symptoms:

- Ruby-only change runs Python/TypeScript/PHP/etc.;
- unrelated lane fails and blocks PR;
- changed paths do not intersect the failed language surface.

Test:

- inspect changed filenames;
- inspect current selector/workflow policy and its tests;
- determine whether fanout is intended closure or accidental over-selection.

Repair the selector/verification ownership logic when incorrect. Do not simply mark unrelated lanes optional without preserving required coverage.

## 3. Runner/toolchain mutation

Symptoms:

- `cargo`, `rustc`, Ruby, PHP, compiler, or generator exists at job start and disappears/changes later;
- failures differ by runner;
- setup jobs modify global host state.

Test runner provisioning and isolation before product code. Prefer immutable/containerized toolchains and per-job state according to current repository guidance.

## 4. Shared build-directory contamination

Symptoms:

- Cargo dep-info parse failures;
- apparently impossible stale object/artifact errors;
- failures appear when multiple self-hosted runners build concurrently;
- different jobs share `target/` or other mutable caches.

Test whether jobs/runners share writable build output. Cache downloads may be shared only when repository design makes them immutable; active build directories should be isolated.

## 5. Container image mismatch

Symptoms:

- compiler rejects flags expected by repository (`-std=gnu++23`, warning flags, etc.);
- local/runner behavior differs after a tooling change;
- PR predates an updated CI image.

Test the image digest/tag and current main workflow before altering code for compiler compatibility.

## 6. FlatBuffers/generated drift

Symptoms:

- BFBS reproducibility, generated-language binding, or schema-aware JSON checks fail;
- generator/toolchain version mismatch;
- generated output changed without source or vice versa.

Use the pinned generator/version and authoritative repository generation command. Do not hand-edit generated output.

## 7. Native SDK/linker failures

Symptoms:

- missing `libsearchkernel_vespa`, `libvespadefaults`, `libxxhash`, RPATH, ABI, or compiler/linker errors;
- runtime dependency resolves outside bundled SDK;
- native cache closure validator fails.

Read current `BUILDING.md`. Separate SDK/provenance defects from Rust/product defects. Check native ABI agreement, dependency closure, RPATH/runtime lookup, pinned compiler/toolchain, and immutable SDK-cache assumptions.

## 8. Dev/doctor/universe harness failures

Symptoms:

- `./dev doctor`, `./dev check`, or `./dev universe` fails before product tests;
- repair/test regexes or provisioning checks fail;
- the harness behaves differently inside/outside the canonical container.

Treat repository harness failures as first-class tooling defects. Do not bypass the harness and declare product CI healthy unless the current repository policy explicitly allows that.

## 9. Exact-head and closure traps

Common false greens:

- reading green checks from the pre-fix head;
- rerun succeeds but branch moved afterward;
- merge succeeds before required adversarial/native verification;
- issue stays open or acceptance criteria remain partially unresolved;
- current main after merge differs from the verified integration result.

Always bind verification to the exact PR head and perform live post-merge reconciliation when SearchKernel CTO rules require it.
