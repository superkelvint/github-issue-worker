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

## CTO gut-check anchors

SearchKernel changes that normally deserve full adversarial review include material changes to lifecycle/concurrency, canonical or portable semantics, schema fidelity and presence semantics, persistence/reopen/compatibility, result fidelity/projection, native ABI/lifetime/error propagation, protocol behavior, architecture boundaries or semantic ownership, and frozen acceptance/verifier behavior.

A prior full adversarial review does not automatically require another full audit after every push. Re-run the full review when the post-review delta changes those high-risk surfaces or materially invalidates the earlier reasoning. Prefer a targeted delta review for narrow tests/docs/mechanical repairs, then record the new exact head.

If the user explicitly asks to adversarially review again, perform it again. If the user explicitly wants an immediate merge, do not invent optional extra audit work for low-risk changes, but do not waive a genuinely required review.

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

If a later commit changes the head, the old marker is stale for exact-head merge evidence. Apply the CTO gut check to decide whether the new head needs a full or delta adversarial review.
