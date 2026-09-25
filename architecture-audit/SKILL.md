---
name: architecture-audit
description: Run a systematic subsystem-wide architecture and correctness audit rather than a PR-only review. Use when asked to audit a code path, subsystem, client, transport, protocol, IR/lowering layer, native boundary, daemon, persistence path, verifier family, or other architectural slice for smells, correctness defects, semantic drift, bypasses, false-green tests, or missing hardening. Batch repository evidence gathering, trace the complete execution path, compare contracts and independent oracles, deduplicate actionable findings against existing issues, and file well-scoped remediation issues when the user asks to record or act on findings.
---

# Architecture Audit

Audit an architectural slice deeply enough to falsify it. A code scan, green CI, or lack of obvious defects is not a clean result.

## Skill boundary

Use this for subsystem-wide review across files/layers. Use `pr-auto` for PR lifecycle, `test-gut-check` for one issue/PR's test adequacy, `coverage-risk` when coverage is the starting point, `issue-reconcile` for queue integrity, and `ci-fixer` for a concrete build/CI/dev failure.

Do not create an implementation branch merely to audit. Findings become bounded issues unless the user explicitly asks to fix them now.

## Modes

- **Report**: audit and report; avoid GitHub mutations unless live repository workflow requires a durable CTO audit record.
- **Record**: audit, deduplicate findings, file only missing remediation issues with complete evidence/labels, and update any required audit ledger.
- **Audit-and-fix**: audit first; fix only bounded findings allowed by current workflow and route larger work into issues.

## Optimize tool use

Use Code Mode (`functions.exec`) to batch independent repository/GitHub reads. Work in stages: authority + subsystem map; implementation/contracts/tests/oracle evidence; targeted follow-up; then issue dedupe/mutations for confirmed findings. Return compact normalized evidence rather than raw payloads.

## Workflow

1. **Resolve the boundary.** Name the subsystem and user-visible capability. Identify every relevant ingress plus semantic, adapter/backend/native/result/transport/client layers. Include adjacent code only when it can bypass, duplicate, or reinterpret audited semantics.
2. **Refresh live authority.** Read applicable `AGENTS.md`, delegated architecture/build/verification docs, and current repository policy. For SearchKernel fetch current CTO `WORKFLOW.md` and product `AGENTS.md` before substantive conclusions.
3. **Load the audit contract.** Read relevant architecture/spec/capability/limitations docs and repository audit checklists. For newly landed/materially changed behavior inspect the implementation delta/history, not only current files.
4. **Trace execution end to end.** Follow validation/defaulting/normalization into canonical meaning, then lowering/execution/results/errors. Look for duplicate semantics, bypasses, alternate paths, silent dropping, fallback, approximation, stale sidecars, and ownership leaks.
5. **Check independent authority.** Use upstream source, frozen oracle, schema/protocol contract, persistent fixture, or another independent source where one exists. If material external behavior cannot be checked, the audit remains incomplete.
6. **Challenge false-green tests.** Ask how current tests/verifiers could pass while behavior is wrong. Exercise relevant malformed/boundary/absence-vs-empty/overflow/Unicode/ordering/reopen/interleaving/unsupported/error-domain/alternate-ingress cases according to blast radius.
7. **Classify findings.** `BLOCKER` prevents closure; `IMPORTANT` is bounded material remediation; `NON_BLOCKING` is limited debt. Use `NO FINDING` only after relevant evidence is complete.
8. **Deduplicate before filing.** Search existing open and recently resolved issues using concrete path/symbol/error/invariant clues. Reuse an issue only when its acceptance scope covers the finding. Verify current `main` before treating a closed issue as resolution evidence.
9. **File bounded remediation when authorized.** One independently reviewable invariant/defect per issue. Include evidence, affected path, expected behavior, forbidden shortcut, and close verification. Apply workflow-state, priority, area, and actual work-type labels in the creation operation; do not use `type:audit` for a bug merely because an audit found it.
10. **Gate the conclusion.** Normalize evidence and run `scripts/audit_policy.py`. Update required audit ledgers only under live workflow/authority. Never call an audit `VERIFIED` solely because no blocker was found.

## SearchKernel

Read `references/searchkernel.md`. Load `implementation-plan/audit/00-audit-method.md`, the relevant subsystem checklist(s), `18-cross-cutting-gates.md` for cross-layer paths, and `19-audit-record-and-freeze.md` when finalizing audit state. For Vespa-owned semantics inspect pinned upstream Vespa or another independent oracle.

## False-green prompts

Challenge whichever apply: alternate ingress bypass; Rust vs portable/gRPC/client disagreement; generated drift; absence/present-empty collapse; malformed/stale/future protocol reaching execution; adapter/native silent dropping; persistence without reopen/history; lifecycle leaks/failure atomicity; fake concurrency tests; result reordering/dropping; error-domain disagreement; mock-only proof for native behavior; source-text assertions instead of runtime behavior; stale-SHA evidence; documentation claiming more than execution proves.

## Report

Use a compact structure:

```text
ARCHITECTURE AUDIT — <scope>
Disposition: BLOCKED | NO BLOCKER FOUND | UNVERIFIED

Blockers / Important findings / Non-blocking
- <finding + evidence + affected invariant + remediation boundary>

False-green challenges
- <challenge + outcome>

Issues
- #123 <new/reused> — <scope>

Evidence gaps
- <anything preventing a stronger conclusion>
```

Omit empty sections. Triage/incomplete work is `UNVERIFIED`.

## Deterministic evidence gate

`scripts/audit_policy.py` requires adversarial depth plus evidence for implementation delta, contract, execution path, independent oracle, layer disagreement checks, negative/boundary cases, false-green challenge, capability claims, fallbacks, and recorded evidence. A blocker yields `BLOCKED`; missing evidence yields `UNVERIFIED`; complete evidence permits `NO_BLOCKER_FOUND`. It never emits `VERIFIED`.

After policy changes run:

```bash
python3 -m unittest discover -s architecture-audit/scripts -p "test_*.py" -v
```
