# SearchKernel PR Auto Notes

Use this reference only for SearchKernel. Current live `WORKFLOW.md`, `AGENTS.md`, `BUILDING.md`, GitHub state, contracts, and executable evidence remain authoritative.

## High-value fleet patterns

Treat these as hypotheses to test, not conclusions:

- PR behind `main` after infrastructure/CI fixes landed -> prefer updating from main before patching the same failure again.
- Language-only change blocked by unrelated language CI -> inspect selector/fanout policy before changing product code.
- Cargo dep-info corruption or impossible stale artifacts across concurrent runners -> inspect shared writable build directories/cache contamination.
- `rustc`, `cargo`, Ruby, PHP, compiler, or generator changes/disappears mid-job -> inspect runner/toolchain provisioning and host mutation.
- C++ rejects expected modern flags -> inspect runner/container compiler mismatch before altering source compatibility.
- BFBS/generated bindings/reproducibility failure -> use pinned authoritative generators; never hand-edit generated output.
- Vespa/native linker/RPATH/ABI/runtime dependency failures -> follow current `BUILDING.md` and native SDK provenance/closure rules.
- `./dev doctor`, `./dev check`, or `./dev universe` failing before product tests -> treat the harness/tooling defect as first-class rather than bypassing it.

## SearchKernel adversarial-review focus

Scale by blast radius. Common falsification targets include:

- lifecycle races and close/reopen behavior;
- malformed/boundary inputs;
- absence vs present-empty semantics;
- persistence and historical reopen compatibility;
- alternate semantic ingress paths;
- portable vs native error-domain consistency;
- generated-artifact drift;
- architectural bypasses or duplicate semantics;
- silent fallback/approximation/dropped fields;
- native ABI ownership/lifetime/error propagation;
- result-tree/projection fidelity;
- stale/unmerged commits that make apparently green evidence irrelevant.

Do not treat a normal diff review as an adversarial review. Record the exact-head marker only after the substantive falsification pass is actually completed.

## Review marker example

```text
<!-- pr-auto:adversarial-review -->
PR-AUTO ADVERSARIAL REVIEW
head_sha: 0123456789abcdef0123456789abcdef01234567
disposition: NO_BLOCKER_FOUND
scope: result projection fidelity and alternate ingress
reviewed_at: 2026-09-25T12:00:00Z
```

If a later commit changes the head, the marker is stale until the new head is reviewed.
